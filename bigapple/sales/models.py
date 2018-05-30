from django.db import models

# Create your models here.

class Customer(models.Model):
    name = models.CharField('name', max_length=200)
    address = models.CharField('address', max_length=200)
    contact_number = models.CharField('contact_number', max_length=45)
    email = models.CharField('email', max_length=200)

    def __str__(self):
        return self.name

class CustomerItem(models.Model):
    item_type = models.CharField('item_type', max_length=200)
    description = models.CharField('description', max_length=200)
    width = models.IntegerField('width')
    length = models.IntegerField('length')
    color = models.CharField('color',  max_length=200)
    gusset = models.CharField('gusset',  max_length=200)
    quantity = models.IntegerField('quantity')
    price = models.IntegerField('price')
    total_amount = models.IntegerField('total_amount')
    # sample_layout = models.CharField('sample_layout', max_length=200)

    def __str__(self):
        return self.item_type

class CustomerPO(models.Model):
    #name = models.CharField('name', max_length=200)
    #address = models.CharField('address', max_length=200) redundant?
    date_issued = models.DateField('date_issued')
    date_required = models.DateField('date_required')
    terms = models.CharField('name', max_length=250)
    other_info = models.CharField('other_info', max_length=250)
    customers = models.ForeignKey(Customer, on_delete=models.CASCADE)
    customer_items = models.ManyToManyField(CustomerItem)

    '''
    def po_number(self):
        return 'PO%s' % (self.)
    '''
