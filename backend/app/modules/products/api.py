import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.config import settings
from app.modules.brand_import.validation import ValidationError, validate_upload
from app.modules.brands.deps import BrandMembership
from app.modules.products.models import (
    Product,
    ProductCategory,
    ProductImage,
    ProductStatus,
    QualityStatus,
)
from app.modules.products.quality import analyze_product_image
from app.modules.products.schemas import (
    ProductCreate,
    ProductImagePublic,
    ProductPublic,
    ProductsPublic,
    ProductUpdate,
)
from app.providers.storage import build_storage_key, get_storage

router = APIRouter(prefix="/brands/{brand_id}/products", tags=["Products"])


def _image_public(image: ProductImage) -> ProductImagePublic:
    return ProductImagePublic(
        id=image.id,
        content_type=image.content_type,
        width=image.width,
        height=image.height,
        is_primary=image.is_primary,
        quality_status=image.quality_status,
        quality_findings_json=image.quality_findings_json,
        created_at=image.created_at,
    )


def _product_public(session: SessionDep, product: Product) -> ProductPublic:
    images = session.exec(
        select(ProductImage).where(ProductImage.product_id == product.id)
    ).all()
    images = sorted(images, key=lambda image: image.created_at)
    return ProductPublic(
        id=product.id,
        brand_id=product.brand_id,
        name=product.name,
        sku=product.sku,
        category=product.category,
        metal_type=product.metal_type,
        metal_color=product.metal_color,
        stone_type=product.stone_type,
        description=product.description,
        integrity_notes=product.integrity_notes,
        status=product.status,
        images=[_image_public(image) for image in images],
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def get_product_or_404(
    session: SessionDep, brand_id: uuid.UUID, product_id: uuid.UUID
) -> Product:
    product = session.get(Product, product_id)
    if not product or product.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("", response_model=ProductsPublic)
def read_products(
    session: SessionDep,
    membership: BrandMembership,
    category: Annotated[ProductCategory | None, Query()] = None,
    include_archived: bool = False,
) -> ProductsPublic:
    statement = select(Product).where(Product.brand_id == membership.brand_id)
    if category:
        statement = statement.where(Product.category == category.value)
    if not include_archived:
        statement = statement.where(Product.status == ProductStatus.ACTIVE.value)
    products = session.exec(statement).all()
    products = sorted(products, key=lambda product: product.created_at, reverse=True)
    data = [_product_public(session, product) for product in products]
    return ProductsPublic(data=data, count=len(data))


@router.post("", response_model=ProductPublic)
def create_product(
    *, session: SessionDep, membership: BrandMembership, product_in: ProductCreate
) -> ProductPublic:
    name = product_in.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Product name is required")
    product = Product(
        brand_id=membership.brand_id,
        name=name,
        category=product_in.category.value,
        sku=product_in.sku,
        metal_type=product_in.metal_type,
        metal_color=product_in.metal_color,
        stone_type=product_in.stone_type,
        description=product_in.description,
        integrity_notes=product_in.integrity_notes,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return _product_public(session, product)


@router.get("/{product_id}", response_model=ProductPublic)
def read_product(
    session: SessionDep, membership: BrandMembership, product_id: uuid.UUID
) -> ProductPublic:
    return _product_public(
        session, get_product_or_404(session, membership.brand_id, product_id)
    )


@router.patch("/{product_id}", response_model=ProductPublic)
def update_product(
    *,
    session: SessionDep,
    membership: BrandMembership,
    product_id: uuid.UUID,
    product_in: ProductUpdate,
) -> ProductPublic:
    product = get_product_or_404(session, membership.brand_id, product_id)
    for field_name, value in product_in.model_dump(exclude_unset=True).items():
        if field_name == "category" and value is not None:
            setattr(product, field_name, value.value if hasattr(value, "value") else value)
        elif field_name == "name":
            if not str(value).strip():
                raise HTTPException(status_code=422, detail="Product name is required")
            product.name = str(value).strip()
        else:
            setattr(product, field_name, value)
    product.updated_at = datetime.now(UTC)
    session.add(product)
    session.commit()
    session.refresh(product)
    return _product_public(session, product)


@router.post("/{product_id}/archive", response_model=ProductPublic)
def archive_product(
    session: SessionDep, membership: BrandMembership, product_id: uuid.UUID
) -> ProductPublic:
    product = get_product_or_404(session, membership.brand_id, product_id)
    product.status = ProductStatus.ARCHIVED.value
    product.updated_at = datetime.now(UTC)
    session.add(product)
    session.commit()
    session.refresh(product)
    return _product_public(session, product)


@router.post("/{product_id}/images", response_model=ProductPublic)
async def upload_product_image(
    session: SessionDep,
    membership: BrandMembership,
    product_id: uuid.UUID,
    file: UploadFile = File(...),
) -> ProductPublic:
    product = get_product_or_404(session, membership.brand_id, product_id)
    data = await file.read(settings.MAX_IMAGE_BYTES + 1)
    if len(data) > settings.MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the size limit")
    try:
        validated = validate_upload(
            file.filename or "product.png", file.content_type, data
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if validated.extension not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(
            status_code=400, detail="Product source images must be PNG, JPEG, or WebP"
        )
    try:
        quality = analyze_product_image(validated.data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    key = build_storage_key(
        membership.brand_id, f"products/{product_id}", validated.filename
    )
    stored = get_storage().save(key, validated.data, validated.content_type)
    existing = session.exec(
        select(ProductImage).where(ProductImage.product_id == product_id)
    ).all()
    image = ProductImage(
        product_id=product_id,
        storage_key=key,
        content_type=stored.content_type,
        width=quality.width,
        height=quality.height,
        is_primary=not any(item.is_primary for item in existing),
        quality_status=quality.status or QualityStatus.OK.value,
        quality_findings_json=quality.findings,
    )
    session.add(image)
    product.updated_at = datetime.now(UTC)
    session.add(product)
    session.commit()
    session.refresh(product)
    return _product_public(session, product)


@router.post("/{product_id}/images/{image_id}/primary", response_model=ProductPublic)
def set_primary_image(
    session: SessionDep,
    membership: BrandMembership,
    product_id: uuid.UUID,
    image_id: uuid.UUID,
) -> ProductPublic:
    product = get_product_or_404(session, membership.brand_id, product_id)
    images = session.exec(
        select(ProductImage).where(ProductImage.product_id == product_id)
    ).all()
    target = next((image for image in images if image.id == image_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Image not found")
    for image in images:
        image.is_primary = image.id == target.id
        session.add(image)
    product.updated_at = datetime.now(UTC)
    session.add(product)
    session.commit()
    session.refresh(product)
    return _product_public(session, product)


@router.get("/{product_id}/images/{image_id}/download")
def download_product_image(
    session: SessionDep,
    membership: BrandMembership,
    product_id: uuid.UUID,
    image_id: uuid.UUID,
) -> Response:
    product = get_product_or_404(session, membership.brand_id, product_id)
    image = session.get(ProductImage, image_id)
    if not image or image.product_id != product.id:
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        data = get_storage().read(image.storage_key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail="Image object not found") from exc
    return Response(
        content=data,
        media_type=image.content_type,
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=300",
        },
    )
