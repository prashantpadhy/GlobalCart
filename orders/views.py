import datetime
from django.shortcuts import redirect, render
from django.http import HttpResponse
from carts.models import Cart,CartItem
from store.models import Product
from .models import Order
from .forms import Orderform
import json
from .models import Payment,OrderProduct
# Create your views here.

def place_order(request,total=0,quantity=0):
    current_user = request.user

    # if cart count is less than zero then redirect to store page

    cart_item = CartItem.objects.filter(user = current_user)
    list_cart_items = list(cart_item)
    cart_count = cart_item.count()

    if cart_count <= 0:
        return redirect('store')
    
    grand_total = 0
    tax = 0
    for cart_item in cart_item:
         total += (cart_item.product.price * cart_item.quantity)
         quantity += cart_item.quantity
    tax = (18 * total)/100
    grand_total = tax + total



    
    if request.method == 'POST':
        form = Orderform(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate Order No
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id) # type: ignore
            data.order_number = order_number 
            data.save()
            order = Order.objects.get(user = current_user, order_number = order_number,is_ordered = False)
            context = {
                'order': order,
                'cart_items' : list_cart_items,
                'grand_total': grand_total,
                'tax' : tax,
                'total': total

            }
            return render(request, 'orders/payments.html',context)
        
    else:
        return redirect('checkout')
    

def payments(request):
   body = json.loads(request.body)
   order = Order.objects.get(user = request.user, order_number = body['orderID'],is_ordered = False)


    
   print(body)
   #    store transaction details in payment model
   payment = Payment(
       user = request.user,
       payment_id = body['transID'],
       payment_method = body['payment_method'],
       amount_paid = order.order_total,
       status = body['status'],


   )
   payment.save()
   order.payment = payment
   order.is_ordered =True
   order.save()

   #    Move the ordered product to ordered table 
   cart_item = CartItem.objects.filter(user = request.user)
   for item in cart_item:

    orderproduct = OrderProduct()
    orderproduct.order = order
    orderproduct.payment = payment
    orderproduct.user = request.user
    orderproduct.product = item.product
    orderproduct.quantity = item.quantity
    orderproduct.product_price = item.product.price
    orderproduct.ordered = True
    orderproduct.save()

    cart_item = CartItem.objects.get(id=item.id)
    product_variation = cart_item.variations.all()
    orderproduct = OrderProduct.objects.get(id = orderproduct.id)
    orderproduct.variations.set(product_variation)
    orderproduct.save()
    #    Reduce the quantily of sold 

    product = Product.objects.get(id = item.product.id)
    product.stock -= item.quantity
    product.save()
# clear the cart
   CartItem.objects.filter(user=request.user).delete()


# send order email to customer
# send transaction and and order number to back to senddata method via json response





   return render(request, 'orders/payments.html') 
    




            

