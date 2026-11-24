import json, secrets
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Product, Category, Setting, Order, OrderItem

def out(data, status=200): return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii':False})
def payload(request):
    try: return json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError): return {}
def setting(key, default=''):
    try: return Setting.objects.get(pk=key).setting_value
    except Setting.DoesNotExist: return default
def csrf_data(): return {'csrf':get_token_dummy()}
def get_token_dummy():
    # get_token requires the current request; populated by each view below.
    return ''
def protected(view):
    from functools import wraps
    @wraps(view)
    def inner(request,*args,**kwargs):
        if not request.user.is_authenticated: return out({'error':'Please login again.'},401)
        return view(request,*args,**kwargs)
    return inner

@ensure_csrf_cookie
@require_http_methods(['GET','POST'])
def auth_api(request):
    if request.method=='GET':
        return out({'loggedIn':request.user.is_authenticated,'username':request.user.username if request.user.is_authenticated else None,'csrf':get_token(request)})
    d=payload(request); action=d.get('action','login')
    if action=='login':
        username=str(d.get('username','')).strip(); password=str(d.get('password',''))
        user=authenticate(request,username=username,password=password)
        if user is None or not user.is_active or not user.is_staff: return out({'error':'Invalid username or password.'},422)
        auth_login(request,user)
        return out({'success':True,'username':user.username,'csrf':get_token(request)})
    if action=='logout':
        if not request.user.is_authenticated: return out({'success':True})
        auth_logout(request); return out({'success':True})
    return out({'error':'Unknown action'},400)

@protected
@require_http_methods(['GET','POST'])
def products_api(request):
    if request.method=='GET':
        all_items=request.GET.get('all')=='1'
        qs=Product.objects.all().order_by('name') if all_items else Product.objects.filter(active=True).order_by('name')
        products=[]
        for p in qs:
            cat=Category.objects.filter(id=p.category_id).first() if p.category_id else None
            products.append({'id':p.id,'name':p.name,'price':str(p.price),'active':int(p.active),'category':cat.name if cat else None})
        return out({'products':products,'categories':list(Category.objects.filter(active=True).order_by('name').values('id','name'))})
    d=payload(request); action=d.get('action')
    if action=='add':
        name=str(d.get('name','')).strip(); price=d.get('price'); cat=d.get('category_id') or None
        try: amount=Decimal(str(price))
        except (InvalidOperation,ValueError): return out({'error':'Enter a valid item name and price.'},422)
        if not name or len(name)>120 or amount<0 or amount>999999: return out({'error':'Enter a valid item name and price.'},422)
        if cat and not Category.objects.filter(id=cat,active=True).exists(): return out({'error':'Invalid category.'},422)
        with connection.cursor() as c: c.execute('INSERT INTO products(category_id,name,price,active) VALUES(%s,%s,%s,1)',[cat,name,amount.quantize(Decimal('.01'))])
        return out({'success':True})
    if action=='toggle':
        try: p=Product.objects.get(id=int(d.get('id',0)))
        except (Product.DoesNotExist,ValueError,TypeError): return out({'error':'Menu item not found.'},404)
        with connection.cursor() as c: c.execute('UPDATE products SET active=1-active WHERE id=%s',[p.id])
        return out({'success':True})
    return out({'error':'Unknown action'},400)

@protected
@require_http_methods(['GET','POST'])
def orders_api(request):
    if request.method=='GET':
        q=request.GET.get('q','').strip(); qs=Order.objects.all().order_by('-id')
        if q: qs=qs.filter(bill_no__icontains=q) | qs.filter(customer_name__icontains=q) | qs.filter(customer_mobile__icontains=q)
        rows=[{'id':o.id,'bill_no':o.bill_no,'customer_name':o.customer_name,'customer_mobile':o.customer_mobile,'grand_total':str(o.grand_total),'payment_method':o.payment_method,'created_at':o.created_at.strftime('%Y-%m-%d %H:%M:%S')} for o in qs[:300]]
        return out({'orders':rows})
    d=payload(request); name=str(d.get('customer_name','')).strip(); mobile=str(d.get('customer_mobile','')).strip(); payment=d.get('payment_method','Cash'); items=d.get('items'); discount_in=d.get('discount',0)
    if not name or len(name)>120 or len(mobile)!=10 or not mobile.isdigit(): return out({'error':'Enter customer name and valid 10-digit mobile number.'},422)
    if payment not in ['Cash','UPI','Card']: return out({'error':'Invalid payment method.'},422)
    if not isinstance(items,list) or not 1<=len(items)<=100: return out({'error':'Add at least one menu item.'},422)
    try: discount_input=Decimal(str(discount_in))
    except (InvalidOperation,ValueError): return out({'error':'Invalid discount.'},422)
    if discount_input<0: return out({'error':'Invalid discount.'},422)
    normalized=[]
    for item in items:
        try: pid=int(item['id']); qty=int(item['qty'])
        except (KeyError,ValueError,TypeError): return out({'error':'Invalid item or quantity.'},422)
        if qty<1 or qty>500: return out({'error':'Invalid item or quantity.'},422)
        normalized.append((pid,qty))
    ids={pid for pid,qty in normalized}; catalog={p.id:p for p in Product.objects.filter(id__in=ids,active=True)}
    if len(catalog)!=len(ids): return out({'error':'A selected menu item is unavailable. Refresh the page.'},422)
    lines=[]; subtotal=Decimal('0.00')
    for pid,qty in normalized:
        p=catalog[pid]; line=(p.price*qty).quantize(Decimal('.01'),rounding=ROUND_HALF_UP); subtotal+=line
        lines.append((pid,p.name,qty,p.price,line))
    subtotal=subtotal.quantize(Decimal('.01')); discount=min(discount_input,subtotal).quantize(Decimal('.01'))
    try: gst_rate=Decimal(setting('gst_rate','5'))
    except InvalidOperation: gst_rate=Decimal('5')
    gst=((subtotal-discount)*gst_rate/Decimal('100')).quantize(Decimal('.01'),rounding=ROUND_HALF_UP); grand=(subtotal-discount+gst).quantize(Decimal('.01'))
    bill_no='MR-'+datetime.now().strftime('%y%m%d')+'-'+secrets.token_hex(3).upper()
    try:
        with transaction.atomic():
            with connection.cursor() as c:
                c.execute('INSERT INTO orders(bill_no,customer_name,customer_mobile,subtotal,discount,gst_rate,gst_amount,grand_total,payment_method,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',[bill_no,name,mobile,subtotal,discount,gst_rate,gst,grand,payment,datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                order_id=c.lastrowid
                for pid,item_name,qty,price,line in lines:
                    c.execute('INSERT INTO order_items(order_id,product_id,item_name,quantity,unit_price,line_total) VALUES(%s,%s,%s,%s,%s,%s)',[order_id,pid,item_name,qty,price,line])
        return out({'success':True,'id':order_id})
    except Exception:
        return out({'error':'Could not save bill. Check database connection and table structure.'},500)

@protected
@require_http_methods(['GET'])
def order_api(request):
    try: oid=int(request.GET.get('id','0')); o=Order.objects.get(id=oid)
    except (ValueError,Order.DoesNotExist): return out({'error':'Bill not found.'},404)
    items=list(OrderItem.objects.filter(order_id=o.id).order_by('id').values('item_name','quantity','unit_price','line_total'))
    for item in items:
        item['unit_price']=str(item['unit_price']); item['line_total']=str(item['line_total'])
    return out({'id':o.id,'bill_no':o.bill_no,'customer_name':o.customer_name,'customer_mobile':o.customer_mobile,'subtotal':str(o.subtotal),'discount':str(o.discount),'gst_rate':str(o.gst_rate),'gst_amount':str(o.gst_amount),'grand_total':str(o.grand_total),'payment_method':o.payment_method,'created_at':o.created_at.strftime('%Y-%m-%d %H:%M:%S'),'items':items,'restaurant':{'restaurant_name':setting('restaurant_name','Mithun Restaurant'),'address':setting('address','Mumbai, Maharashtra, India'),'phone':setting('phone',''),'gstin':setting('gstin','')}})

@protected
@require_http_methods(['GET','POST'])
def settings_api(request):
    keys=['restaurant_name','address','phone','gstin','gst_rate']
    if request.method=='GET': return out({k:setting(k,'Mithun Restaurant' if k=='restaurant_name' else ('5' if k=='gst_rate' else '')) for k in keys})
    d=payload(request); vals={k:str(d.get(k,'')).strip() for k in keys}; vals['gstin']=vals['gstin'].upper()
    try: rate=Decimal(vals['gst_rate'])
    except InvalidOperation: return out({'error':'Enter a restaurant name and valid GST percentage.'},422)
    if not vals['restaurant_name'] or rate<0 or rate>100: return out({'error':'Enter a restaurant name and valid GST percentage.'},422)
    with connection.cursor() as c:
        for k,v in vals.items(): c.execute('INSERT INTO settings(setting_key,setting_value) VALUES(%s,%s) ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value)',[k,v])
    return out({'success':True})
