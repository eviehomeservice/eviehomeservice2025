import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import ServiceCategory, Order
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.dateparse import parse_date
from datetime import date
from django.http import JsonResponse
from secrets import token_hex

def service_list(request):
    services = ServiceCategory.objects.all()
    user_orders = []
    submitted_phone = ''

    # 从 POST 或 Cookie 获取手机号
    if request.method == 'POST' and 'contact_phone' in request.POST:
        submitted_phone = request.POST.get('contact_phone', '').strip()
        user_orders = Order.objects.filter(contact_phone=submitted_phone).order_by('-created_at')
        response = render(request, 'service_app/service_list.html', {
            'services': services,
            'user_orders': user_orders,
            'submitted_phone': submitted_phone
        })
        # 写入 cookie，保存 30 天
        response.set_cookie('contact_phone', submitted_phone, max_age=30*24*60*60)
        return response
    else:
        submitted_phone = request.COOKIES.get('contact_phone', '')
        if submitted_phone:
            user_orders = Order.objects.filter(contact_phone=submitted_phone).order_by('-created_at')

    return render(request, 'service_app/service_list.html', {
        'services': services,
        'user_orders': user_orders,
        'submitted_phone': submitted_phone
    })

def user_service(request, service_id):
    service = get_object_or_404(ServiceCategory, pk=service_id)
    return render(request, 'service_app/user_service.html', {'service': service})

def create_order(request, service_id):
    service = get_object_or_404(ServiceCategory, pk=service_id)

    if request.method == 'POST':
        try:
            # 生成唯一订单 token
            order_token = token_hex(8)
           
            # 将数据暂存于 session
            request.session['pending_order'] = {
                'service_id': service.id,
                'customer_name': request.POST.get('customer_name', '').strip(),
                'service_date': request.POST.get('service_date', '').strip(),
                'service_address': request.POST.get('service_address', '').strip(),
                'contact_phone': request.POST.get('contact_phone', '').strip(),
                'contact_email': request.POST.get('contact_email', '').strip(),
                'contact_wechat': request.POST.get('contact_wechat', '').strip(),
                'notes': request.POST.get('notes', '').strip(),
                'final_price': str(service.fixed_price if service.fixed_price else service.prepay_amount),
                'order_token': order_token
            }
            return redirect('view_order', order_token=order_token)

        except Exception as e:
            messages.error(request, f"创建订单失败: {str(e)}")
            return redirect('user_service', service_id=service_id)

    return redirect('user_service', service_id=service_id)

def view_order(request, order_token):
    # 尝试先获取已保存订单
    try:
        order = Order.objects.get(order_token=order_token)
    except Order.DoesNotExist:
        order = None

    if request.method == 'POST':
        if 'payment_proof' in request.FILES:
            payment_proof = request.FILES['payment_proof']

            # 若订单尚未创建，则从 session 获取信息并创建
            if not order:
                data = request.session.get('pending_order')
                if not data or data['order_token'] != order_token:
                    messages.error(request, "订单信息已过期，请重新提交。")
                    return redirect('service_list')

                service = get_object_or_404(ServiceCategory, id=data['service_id'])

                order = Order.objects.create(
                    service=service,
                    customer_name=data['customer_name'],
                    service_date=data['service_date'],
                    service_address=data['service_address'],
                    contact_phone=data['contact_phone'],
                    contact_email=data['contact_email'],
                    contact_wechat=data['contact_wechat'],
                    notes=data['notes'],
                    final_price=data['final_price'],
                    payment_proof=payment_proof,
                    order_token=order_token,
                    status='in_progress'
                )
                del request.session['pending_order']
            else:
                order.payment_proof = payment_proof
                order.status = 'in_progress'
                order.save()

            messages.success(request, "支付凭证已上传成功")
            return redirect('view_order', order_token=order_token)
        else:
            messages.error(request, "请选择支付凭证文件")

    return render(request, 'service_app/user_order.html', {'order': order})


@staff_member_required
def admin_dashboard(request):
    orders = Order.objects.all().order_by('-created_at')
    services = ServiceCategory.objects.all()
    return render(request, 'service_app/admin_dashboard.html', {
        'orders': orders,
        'services': services
    })

@staff_member_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        if 'accept_order' in request.POST:
            order.status = 'confirmed'
            order.save()
        elif 'update_quotation' in request.POST:
            order.final_price = request.POST.get('final_price')
            order.quotation_proof = request.FILES.get('quotation_proof')
            order.status = 'payment'
            order.save()
        elif 'complete_order' in request.POST:
            order.status = 'completed'
            order.save()
        return redirect('admin_dashboard')
    
    return render(request, 'service_app/order_detail.html', {'order': order})

@staff_member_required
def create_service(request):
    if request.method == 'POST':
        service = ServiceCategory(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            steps=request.POST.get('steps'),
            notes=request.POST.get('notes', ''),
            fixed_price=request.POST.get('fixed_price') or None,
            prepay_amount=request.POST.get('prepay_amount') or None,
            currency=request.POST.get('currency', 'CAD'),
            provider_name=request.POST.get('provider_name'),
            provider_contact=request.POST.get('provider_contact'),
            provider_email=request.POST.get('provider_email', ''),
            provider_wechat=request.POST.get('provider_wechat', ''),
            provider_phone=request.POST.get('provider_phone', '')
        )
        service.save()
        return redirect('admin_dashboard')
    
    return render(request, 'service_app/create_service.html')

@staff_member_required
def edit_service(request, service_id):
    service = get_object_or_404(ServiceCategory, pk=service_id)
    
    if request.method == 'POST':
        service.name = request.POST.get('name')
        service.description = request.POST.get('description')
        service.steps = request.POST.get('steps')
        service.notes = request.POST.get('notes', '')
        service.fixed_price = request.POST.get('fixed_price') or None
        service.prepay_amount = request.POST.get('prepay_amount') or None
        service.currency = request.POST.get('currency', 'CAD')
        service.provider_name = request.POST.get('provider_name')
        service.provider_contact = request.POST.get('provider_contact')
        service.provider_email = request.POST.get('provider_email', '')
        service.provider_wechat = request.POST.get('provider_wechat', '')
        service.provider_phone = request.POST.get('provider_phone', '')
        service.save()
        return redirect('admin_dashboard')
    
    return render(request, 'service_app/edit_service.html', {'service': service})

@staff_member_required
def accept_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.status = 'in_progress'
        order.save()
    return redirect('admin_dashboard')

@staff_member_required
def complete_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.status = 'completed'
        order.save()
    return redirect('admin_dashboard')

@staff_member_required
def user_complete_order(request, order_token):
    order = get_object_or_404(Order, order_token=order_token)
    if request.method == 'POST' and order.status == 'completed':
        order.rating = request.POST.get('rating')
        order.feedback = request.POST.get('feedback', '')
        order.save()
    return redirect('view_order', order_token=order_token)

def api_order_detail(request, order_token):
    try:
        order = Order.objects.select_related('service').get(order_token=order_token)
        data = {
            'service_name': order.service.name,
            'status': order.status,
            'status_display': order.get_status_display(),
            'order_token': order.order_token,
            'customer_name': order.customer_name,
            'service_date': order.service_date.strftime('%Y-%m-%d'),
            'service_address': order.service_address,
            'final_price': str(order.final_price or '0.00'),
            'currency': order.service.currency,
            'contact_phone': order.contact_phone,
            'contact_wechat': order.contact_wechat,
            'contact_email': order.contact_email,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'provider_name': order.service.provider_name,
            'notes': order.notes,
            'payment_proof_url': order.payment_proof.url if order.payment_proof else None,
        }
        return JsonResponse(data)
    except Order.DoesNotExist:
        return JsonResponse({'error': '订单不存在'}, status=404)
