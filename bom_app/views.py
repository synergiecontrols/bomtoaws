from io import BytesIO
from django.shortcuts import render
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import viewsets
from .models import Item
from .serializers import ItemSerializer
from rest_framework.decorators import api_view
from .serializers import RegisterSerializer
from django.contrib.auth import authenticate, login as auth_login
from rest_framework_simplejwt.tokens import RefreshToken



# Create your views here.


@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse({'status': 'User created'})
    return JsonResponse(serializer.errors)

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        auth_login(request, user)
        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username':  username
        })
    return JsonResponse({'error': 'Invalid credentials'})


@api_view(['POST'])
def logout(request):
    # This view doesn't need to do anything with tokens, as JWTs are stateless
    # Just instruct the client to delete the token from local storage
    return JsonResponse({'message': 'Successfully logged out'})

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def get_queryset(self):
        head = self.request.query_params.get('head', None)
        if head:
            return Item.objects.filter(head=head)
        return Item.objects.all()

    def create(self, request, *args, **kwargs):
        print("Received data:", request.data)
        return super().create(request, *args, **kwargs)



@csrf_exempt  # Disable CSRF protection for simplicity (only in development)

def delete_items(request):    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_name = data.get('mat_name')

            if not material_name:
                return JsonResponse({'error': 'material name not found'})
            
            item = Item.objects.filter(mat_name=material_name).first()

            if item:
                item.delete()  # Delete the item if it exists
                return JsonResponse({'status': 'success', 'message': f'Item with make "{material_name}" Updated succesfully'}, status=200)
            else:
                return JsonResponse({'status': 'failed', 'error': 'Item not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'failed', 'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'failed', 'error': 'Invalid request method'}, status=405)



@csrf_exempt  # Disable CSRF protection for simplicity (only in development)

def update_price(request):    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_name = data.get('mat_name')

            
            list_price = data.get('new_price')
            



            if not material_name:
                return JsonResponse({'error': 'material name not found'})
            
            item = Item.objects.filter(mat_name=material_name).first()

            if item:
                item.least_price =   list_price
                item.save()
                return JsonResponse({'status': 'success', 'message': f'Item with make "{material_name}" deleted'}, status=200)
            else:
                return JsonResponse({'status': 'failed', 'error': 'Item not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'failed', 'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'failed', 'error': 'Invalid request method'}, status=405)



@csrf_exempt  # Disable CSRF protection for simplicity (only in development)
def submit_create_bom(request):
    if request.method == 'POST':
        try:
            # Parse the received JSON data
            data = json.loads(request.body)

            # Convert the list of dictionaries into a DataFrame
            df = pd.DataFrame(data)
            df['total_unit_price'] = pd.to_numeric( df['total_unit_price'])
            total_sum = round(df['total_unit_price'].sum(),2)

            # Manually set column names (in the order you want)
            column_headers = {
                'mat_name': 'MATERIAL NAME',
                'type_no': 'TYPE NUMBER',
                'make': 'MAKE',
                'head': 'HEAD',
                'quantity': 'QUANTITY',
                'least_price': 'LIST PRICE',
                'discount': 'DISCOUNT (%)',
                'final_price': 'FINAL PRICE',
                'total_unit_price': 'TOTAL UNIT PRICE'
            }

            # Rename DataFrame columns
            df.rename(columns=column_headers, inplace=True)
            
            # Convert all text columns to uppercase
            df = df.applymap(lambda x: x.upper() if isinstance(x, str) else x)

            total_row = pd.DataFrame(
                {
                    'MATERIAL NAME': [''],
                    'TYPE NUMBER': [''],
                    'MAKE': [''],
                    'HEAD': [''],
                    'QUANTITY': [''],
                    'LIST PRICE': [''],
                    'DISCOUNT (%)': [''],
                    'FINAL PRICE': ['TOTAL SUM'],
                    'TOTAL UNIT PRICE': [total_sum]
                }
            )

            # Append the total row to the DataFrame
            df = pd.concat([df, total_row], ignore_index=True)


            # Use a BytesIO buffer to save the Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, columns=list(column_headers.values()))

            # Rewind the buffer
            output.seek(0)

            # Create a downloadable response with Excel data
            response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=bom_file.xlsx'
            return response

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


