from django.db import models
class Setting(models.Model):
    setting_key=models.CharField(max_length=80,primary_key=True); setting_value=models.CharField(max_length=255)
    class Meta: db_table='settings'; managed=False
class Category(models.Model):
    id=models.AutoField(primary_key=True); name=models.CharField(max_length=80); active=models.BooleanField(default=True)
    class Meta: db_table='categories'; managed=False
class Product(models.Model):
    id=models.AutoField(primary_key=True); category_id=models.IntegerField(null=True); name=models.CharField(max_length=120); price=models.DecimalField(max_digits=10,decimal_places=2); active=models.BooleanField(default=True)
    class Meta: db_table='products'; managed=False
class Order(models.Model):
    id=models.BigAutoField(primary_key=True); bill_no=models.CharField(max_length=40,unique=True); customer_name=models.CharField(max_length=120); customer_mobile=models.CharField(max_length=15); subtotal=models.DecimalField(max_digits=10,decimal_places=2); discount=models.DecimalField(max_digits=10,decimal_places=2); gst_rate=models.DecimalField(max_digits=5,decimal_places=2); gst_amount=models.DecimalField(max_digits=10,decimal_places=2); grand_total=models.DecimalField(max_digits=10,decimal_places=2); payment_method=models.CharField(max_length=10); created_at=models.DateTimeField()
    class Meta: db_table='orders'; managed=False
class OrderItem(models.Model):
    id=models.BigAutoField(primary_key=True); order_id=models.BigIntegerField(); product_id=models.IntegerField(null=True); item_name=models.CharField(max_length=120); quantity=models.IntegerField(); unit_price=models.DecimalField(max_digits=10,decimal_places=2); line_total=models.DecimalField(max_digits=10,decimal_places=2)
    class Meta: db_table='order_items'; managed=False
