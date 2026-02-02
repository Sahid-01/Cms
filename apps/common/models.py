"""
Abstract base models for Django projects.
These models provide common fields for auditing, timestamps, and soft delete functionality.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class TimestampModel(models.Model):
    """
    Abstract model that provides timestamp fields.
    
    Fields:
        - created_at: Automatically set when the object is first created
        - updated_at: Automatically updated whenever the object is saved
    
    Usage:
        class MyModel(TimestampModel):
            name = models.CharField(max_length=100)
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        help_text="Timestamp when the record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        help_text="Timestamp when the record was last updated"
    )

    class Meta:
        abstract = True  # This model won't create a database table
        ordering = ['-created_at']  # Default ordering by newest first


class AuditModel(models.Model):
    """
    Abstract model that tracks who created and updated records.
    
    Fields:
        - created_by: Foreign key to the user who created the record
        - updated_by: Foreign key to the user who last updated the record
    
    Note: Uses settings.AUTH_USER_MODEL to reference your User model.
    Both fields are optional (null=True) for system-generated records.
    
    Usage:
        class MyModel(AuditModel):
            name = models.CharField(max_length=100)
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        help_text="User who created this record"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        help_text="User who last updated this record"
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract model that provides soft delete functionality.
    
    Fields:
        - is_deleted: Boolean flag indicating if the record is deleted
        - deleted_at: Timestamp when the record was deleted
    
    Instead of actually deleting records from the database, this model
    allows you to mark them as deleted. This is useful for:
        - Data recovery
        - Audit trails
        - Maintaining referential integrity
        - Compliance requirements
    
    Usage:
        class MyModel(SoftDeleteModel):
            name = models.CharField(max_length=100)
        
        # Soft delete
        obj = MyModel.objects.get(id=1)
        obj.delete()  # or obj.soft_delete()
        
        # Get only active (not deleted) records
        active_objects = MyModel.objects.filter(is_deleted=False)
    """
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,  # Index for faster queries
        help_text="Indicates if this record has been soft deleted"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the record was deleted"
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        """Mark the record as deleted without removing it from database."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class BaseModel(TimestampModel, AuditModel, SoftDeleteModel):
    """
    Complete abstract base model combining all audit functionality.
    
    Includes:
        - created_at, updated_at (from TimestampModel)
        - created_by, updated_by (from AuditModel)
        - is_deleted, deleted_at (from SoftDeleteModel)
    
    This is the recommended base class for most models in your project.
    
    Usage:
        from .base_models import BaseModel
        
        class Product(BaseModel):
            name = models.CharField(max_length=100)
            price = models.DecimalField(max_digits=10, decimal_places=2)
            
        # All audit fields are automatically included:
        product = Product.objects.create(
            name="Laptop",
            price=999.99,
            created_by=request.user
        )
    """
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


# Optional: Custom Manager for filtering out soft-deleted records by default
class ActiveManager(models.Manager):
    """
    Custom manager that excludes soft-deleted records by default.
    
    Usage:
        class Product(BaseModel):
            name = models.CharField(max_length=100)
            
            objects = models.Manager()  # Default manager (includes deleted)
            active = ActiveManager()     # Only non-deleted records
        
        # Get all products including deleted
        all_products = Product.objects.all()
        
        # Get only active products
        active_products = Product.active.all()
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class DeletedManager(models.Manager):
    """
    Custom manager that returns only soft-deleted records.
    
    Usage:
        class Product(BaseModel):
            name = models.CharField(max_length=100)
            
            objects = models.Manager()    # All records
            active = ActiveManager()       # Active only
            deleted = DeletedManager()     # Deleted only
        
        # Get only deleted products
        deleted_products = Product.deleted.all()
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=True)