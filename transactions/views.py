from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db import models
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from decimal import Decimal
from .models import Transaction
from .forms import AddMoneyForm, TransferByMobileForm, TransferByAccountForm, StatementFilterForm
from banking.models import Account

User = get_user_model()

@login_required
def add_money(request):
    # Check if user has an account
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    if request.method == 'POST':
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', 'Self deposit')
            
            # Create transaction and update balance
            with transaction.atomic():
                user_account = request.user.account
                user_account.balance += amount
                user_account.save()
                
                Transaction.objects.create(
                    from_account=None,  # No source for deposits
                    to_account=user_account,
                    amount=amount,
                    transaction_type='Deposit',
                    status='Success',
                    description=description or 'Self deposit',
                    balance_after=user_account.balance,
                    account=user_account
                )
            
            messages.success(request, f'₹{amount} has been added to your account successfully!')
            return redirect('banking:view_balance')
    else:
        form = AddMoneyForm()
    
    return render(request, 'transactions/add_money.html', {'form': form})


@login_required
def transfer_money(request):
    # Check if user has an account
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    mobile_form = TransferByMobileForm()
    account_form = TransferByAccountForm()
    
    if request.method == 'POST':
        transfer_method = request.POST.get('transfer_method')
        
        if transfer_method == 'mobile':
            mobile_form = TransferByMobileForm(request.POST)
            if mobile_form.is_valid():
                phone_number = mobile_form.cleaned_data['phone_number']
                amount = mobile_form.cleaned_data['amount']
                description = mobile_form.cleaned_data.get('description', '')
                
                # Get recipient account by phone number
                try:
                    recipient_account = Account.objects.get(phone_number=phone_number)
                except Account.DoesNotExist:
                    messages.error(request, 'No account found with this phone number.')
                    return render(request, 'transactions/transfer_money.html', {
                        'mobile_form': mobile_form,
                        'account_form': account_form
                    })
                
                # Check if user is trying to transfer to themselves
                if recipient_account == request.user.account:
                    messages.error(request, 'You cannot transfer money to yourself.')
                    return render(request, 'transactions/transfer_money.html', {
                        'mobile_form': mobile_form,
                        'account_form': account_form
                    })
                
                # Check if user has sufficient balance
                if request.user.account.balance < amount:
                    messages.error(request, 'Insufficient balance.')
                    return render(request, 'transactions/transfer_money.html', {
                        'mobile_form': mobile_form,
                        'account_form': account_form
                    })
                
                # Process transfer
                with transaction.atomic():
                    sender_account = request.user.account
                    sender_account.balance -= amount
                    sender_account.save()
                    
                    recipient_account.balance += amount
                    recipient_account.save()
                    
                    # Create transaction record for sender (outgoing)
                    Transaction.objects.create(
                        from_account=sender_account,
                        to_account=recipient_account,
                        amount=amount,
                        transaction_type='Transfer',
                        status='Success',
                        description=description or f'Transfer to {recipient_account.account_holder_name}',
                        balance_after=sender_account.balance,
                        account=sender_account
                    )
                    
                    # Create transaction record for recipient (incoming)
                    Transaction.objects.create(
                        from_account=sender_account,
                        to_account=recipient_account,
                        amount=amount,
                        transaction_type='Transfer',
                        status='Success',
                        description=description or f'Transfer from {sender_account.account_holder_name}',
                        balance_after=recipient_account.balance,
                        account=recipient_account
                    )
                
                messages.success(request, f'₹{amount} transferred successfully to {recipient_account.account_holder_name}!')
                return redirect('transactions:transaction_history')
        
        elif transfer_method == 'account':
            account_form = TransferByAccountForm(request.POST)
            if account_form.is_valid():
                account_number = account_form.cleaned_data['account_number']
                ifsc_code = account_form.cleaned_data['ifsc_code']
                amount = account_form.cleaned_data['amount']
                description = account_form.cleaned_data.get('description', '')
                
                # Get recipient account
                recipient_account = Account.objects.get(
                    account_number=account_number,
                    ifsc_code=ifsc_code
                )
                
                # Check if user is trying to transfer to themselves
                if recipient_account == request.user.account:
                    messages.error(request, 'You cannot transfer money to yourself.')
                    return render(request, 'transactions/transfer_money.html', {
                        'mobile_form': mobile_form,
                        'account_form': account_form
                    })
                
                # Check if user has sufficient balance
                if request.user.account.balance < amount:
                    messages.error(request, 'Insufficient balance.')
                    return render(request, 'transactions/transfer_money.html', {
                        'mobile_form': mobile_form,
                        'account_form': account_form
                    })
                
                # Process transfer
                with transaction.atomic():
                    sender_account = request.user.account
                    sender_account.balance -= amount
                    sender_account.save()
                    
                    recipient_account.balance += amount
                    recipient_account.save()
                    
                    # Create transaction record for sender (outgoing)
                    Transaction.objects.create(
                        from_account=sender_account,
                        to_account=recipient_account,
                        amount=amount,
                        transaction_type='Transfer',
                        status='Success',
                        description=description or f'Transfer to {recipient_account.account_holder_name}',
                        balance_after=sender_account.balance,
                        account=sender_account
                    )
                    
                    # Create transaction record for recipient (incoming)
                    Transaction.objects.create(
                        from_account=sender_account,
                        to_account=recipient_account,
                        amount=amount,
                        transaction_type='Transfer',
                        status='Success',
                        description=description or f'Transfer from {sender_account.account_holder_name}',
                        balance_after=recipient_account.balance,
                        account=recipient_account
                    )
                
                messages.success(request, f'₹{amount} transferred successfully to {recipient_account.account_holder_name}!')
                return redirect('transactions:transaction_history')
    
    return render(request, 'transactions/transfer_money.html', {
        'mobile_form': mobile_form,
        'account_form': account_form
    })


@login_required
def transaction_history(request):
    # Check if user has an account
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    user_account = request.user.account
    
    # Get all transactions for this account's ledger
    transactions = Transaction.objects.filter(
        account=user_account
    ).order_by('-timestamp')
    
    # Apply search and filters
    from .forms import TransactionSearchForm
    search_form = TransactionSearchForm(request.GET or None)
    
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        transaction_type = search_form.cleaned_data.get('transaction_type')
        min_amount = search_form.cleaned_data.get('min_amount')
        max_amount = search_form.cleaned_data.get('max_amount')
        
        # Apply search filter
        if search_query:
            transactions = transactions.filter(description__icontains=search_query)
        
        # Apply type filter
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Apply amount range filters
        if min_amount is not None:
            transactions = transactions.filter(amount__gte=min_amount)
        if max_amount is not None:
            transactions = transactions.filter(amount__lte=max_amount)
    
    return render(request, 'transactions/transaction_history.html', {
        'transactions': transactions,
        'search_form': search_form,
    })


@login_required
def statement(request):
    # Check if user has an account
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    user_account = request.user.account
    form = StatementFilterForm(request.GET or None)
    
    # Get all transactions for this account's ledger
    transactions = Transaction.objects.filter(
        account=user_account
    ).order_by('-timestamp')
    
    start_date = None
    end_date = None
    
    # Apply date filters if provided
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if start_date:
            transactions = transactions.filter(timestamp__date__gte=start_date)
        if end_date:
            transactions = transactions.filter(timestamp__date__lte=end_date)
    
    # Calculate totals
    total_credits = sum([float(t.amount) for t in transactions if t.to_account == user_account])
    total_debits = sum([float(t.amount) for t in transactions if t.from_account == user_account])
    
    return render(request, 'transactions/statement.html', {
        'transactions': transactions,
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'total_credits': total_credits,
        'total_debits': total_debits,
    })


@login_required
def generate_statement_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from datetime import datetime
    
    # Check if user has an account
    if not hasattr(request.user, 'account'):
        messages.error(request, 'You need to create a bank account first.')
        return redirect('banking:create_account')
    
    user_account = request.user.account
    
    # Get date filters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Get all transactions for this account's ledger
    transactions = Transaction.objects.filter(
        account=user_account
    ).order_by('timestamp')
    
    # Apply date filters if provided
    if start_date:
        from datetime import datetime
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        transactions = transactions.filter(timestamp__date__gte=start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        transactions = transactions.filter(timestamp__date__lte=end_date_obj)
    
    # Calculate totals
    total_credits = sum([float(t.amount) for t in transactions if t.to_account == user_account])
    total_debits = sum([float(t.amount) for t in transactions if t.from_account == user_account])
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    filename = f'statement_{user_account.account_number}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create the PDF object
    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)
    
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0F766E'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0F766E'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    
    # Add bank logo/name
    bank_name = Paragraph('<b>ASTRALFIN</b> Neo Bank', title_style)
    elements.append(bank_name)
    elements.append(Spacer(1, 12))
    
    # Add statement title
    statement_title = Paragraph('Account Statement', heading_style)
    elements.append(statement_title)
    elements.append(Spacer(1, 20))
    
    # Account Information
    account_info_data = [
        ['Account Holder:', user_account.account_holder_name],
        ['Account Number:', user_account.account_number],
        ['IFSC Code:', user_account.ifsc_code],
        ['Customer ID:', user_account.customer_id],
        ['Statement Date:', datetime.now().strftime('%d %B, %Y')],
    ]
    
    if start_date and end_date:
        period_text = f"{start_date_obj.strftime('%d %b, %Y')} to {end_date_obj.strftime('%d %b, %Y')}"
    elif start_date:
        period_text = f"From {start_date_obj.strftime('%d %b, %Y')}"
    elif end_date:
        period_text = f"Till {end_date_obj.strftime('%d %b, %Y')}"
    else:
        period_text = 'All Time'
    
    account_info_data.append(['Period:', period_text])
    
    account_info_table = Table(account_info_data, colWidths=[2*inch, 4*inch])
    account_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0F2F1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(account_info_table)
    elements.append(Spacer(1, 20))
    
    # Summary Section
    summary_heading = Paragraph('Summary', heading_style)
    elements.append(summary_heading)
    elements.append(Spacer(1, 10))
    
    summary_data = [
        ['Total Credits', f'₹{total_credits:.2f}'],
        ['Total Debits', f'₹{total_debits:.2f}'],
        ['Current Balance', f'₹{float(user_account.balance):.2f}'],
        ['Total Transactions', str(transactions.count())],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FDFA')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Transaction Details
    if transactions.exists():
        transaction_heading = Paragraph('Transaction Details', heading_style)
        elements.append(transaction_heading)
        elements.append(Spacer(1, 10))
        
        # Transaction table header
        transaction_data = [
            ['Date', 'Description', 'Debit', 'Credit', 'Balance']
        ]
        
        # Add transaction rows
        for txn in transactions:
            date_str = txn.timestamp.strftime('%d %b, %Y\n%I:%M %p')
            
            # Determine description
            if txn.transaction_type == 'Deposit':
                desc = 'Money Added'
            elif txn.to_account == user_account:
                desc = f'From {txn.from_account.account_holder_name}' if txn.from_account else 'Credit'
            else:
                desc = f'To {txn.to_account.account_holder_name}' if txn.to_account else 'Debit'
            
            if txn.description:
                desc += f'\n{txn.description[:30]}...' if len(txn.description) > 30 else f'\n{txn.description}'
            
            # Determine debit/credit
            if txn.to_account != user_account and txn.transaction_type != 'Deposit':
                debit = f'₹{float(txn.amount):.2f}'
                credit = '-'
            else:
                debit = '-'
                credit = f'₹{float(txn.amount):.2f}'
            
            balance = f'₹{float(txn.balance_after):.2f}' if txn.balance_after else '-'
            
            transaction_data.append([date_str, desc, debit, credit, balance])
        
        # Create transaction table
        transaction_table = Table(transaction_data, 
                                 colWidths=[1.2*inch, 2.2*inch, 1*inch, 1*inch, 1.1*inch])
        
        transaction_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F766E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Body styling
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        
        elements.append(transaction_table)
    else:
        no_txn_text = Paragraph('<i>No transactions found for the selected period.</i>', normal_style)
        elements.append(no_txn_text)
    
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_text = Paragraph(
        '<i>This is a computer-generated statement and does not require a signature.<br/>'
        'For any queries, please contact ASTRALFIN support.</i>',
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    )
    elements.append(footer_text)
    
    # Build PDF
    doc.build(elements)
    
    return response
