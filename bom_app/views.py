from io import BytesIO
from rest_framework.exceptions import ValidationError
from django.shortcuts import render

import os
from openpyxl import Workbook
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import viewsets
from .models import Item ,ProjectDetails
from .serializers import ItemSerializer
from rest_framework.decorators import api_view
from .serializers import RegisterSerializer
from django.contrib.auth import authenticate, login as auth_login
from rest_framework_simplejwt.tokens import RefreshToken
from openpyxl.styles import NamedStyle
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
from django.db import IntegrityError
from rest_framework import status
from datetime import date



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
        try:
            # Try to create the item using the parent class's create method
            # print("Data received from frontend:", request.data)
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            # If the error is related to the 'type_no' field, raise a ValidationError
            if 'type_no' in str(e):
                raise ValidationError({"detail": "A record with this 'type_no' already exists."})
            # For other IntegrityError cases, raise a generic error
            raise ValidationError({"detail": str(e)})
        except Exception as e:
            # Log and return other exceptions
            raise ValidationError({"detail": "A record with this 'type_no' already exists."})



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

def update_items(request):
    data = json.loads(request.body)
    try:
        item = Item.objects.get(id=data['id'])
        item.mat_name = data.get('mat_name', item.mat_name)
        item.type_no = data.get('type_no', item.type_no)
        item.make = data.get('make', item.make)
        item.head = data.get('head', item.head)
        item.least_price = data.get('least_price', item.least_price)
        item.discount = data.get('discount', item.discount)
        item.save()
        return JsonResponse({"success": "Item updated successfully"})
    except Item.DoesNotExist:
        return JsonResponse({"error": "Item not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG to capture all log levels
logger = logging.getLogger(__name__)



@csrf_exempt  # Disable CSRF protection for simplicity (only in development)
def submit_create_bom(request):
    if request.method == 'POST':
        try:
            # Parse the received JSON data
            data = json.loads(request.body)
            # print("Received Data:", data)

            # Extract filename and BOM data
            filename = data.get('fileName', 'bom_file.xlsx')
            bom_data = data.get('items', [])
            df = pd.DataFrame(bom_data)

            # Define column headers for renaming
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

            # Rename columns
            df.rename(columns=column_headers, inplace=True)

            # Normalize and map HEAD column
            head_mapping = {
                "plchw":'PLC_HW',
                "nwcom":'NW COM',
                'drvsw': 'DRV_SW',
                'swgr': 'SWGR',
                "bought":'BOUGHT',
                "magnitics":'MAGNITICS',
                "panels":'PANELS',
                'wiresandcable': 'WIRES & CABLE',
                "terminals":'TERMINALS',
                "class_c":'CLASS_C',   
                "busbar":'BUSBAR',
                
                # Add other mappings as needed
            }
            df['HEAD'] = df['HEAD'].str.lower().map(head_mapping).fillna(df['HEAD'])

            # Apply uppercase to all string columns
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].str.upper()

            # Define the custom order for the 'HEAD' column
            head_order = [
                'PLC_HW', 'NW COM', 'DRV_SW', 'SWGR', 'BOUGHT', 'MAGNITICS',
                'PANELS', 'WIRES & CABLE', 'TERMINALS', 'CLASS_C', 'BUSBAR'
            ]

            # Sort the DataFrame based on the custom 'HEAD' order
            df['HEAD'] = pd.Categorical(df['HEAD'], categories=head_order, ordered=True)
            df = df.sort_values(by='HEAD')

            # Specify column order explicitly for the Excel output
            output_columns = [
                'MATERIAL NAME',
                'TYPE NUMBER',
                'MAKE',
                'HEAD',
                'QUANTITY',
                'LIST PRICE',
                'DISCOUNT (%)',
                'FINAL PRICE',
                'TOTAL UNIT PRICE'
            ]

            # Use a BytesIO buffer to save the Excel file in memory
            output = BytesIO()

            # Create an Excel writer using openpyxl engine
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, columns=output_columns)

                # Access the workbook and the active sheet
                workbook = writer.book
                worksheet = workbook.active

                # Add formulas for `FINAL PRICE` and `TOTAL UNIT PRICE`
                for row in range(2, len(df) + 2):  # Start from row 2 (Excel is 1-indexed)
                    quantity_cell = f"E{row}"  # QUANTITY column
                    list_price_cell = f"F{row}"  # LIST PRICE column
                    discount_cell = f"G{row}"  # DISCOUNT (%) column
                    final_price_cell = f"H{row}"  # FINAL PRICE column
                    total_unit_price_cell = f"I{row}"  # TOTAL UNIT PRICE column

                    # Formula for FINAL PRICE: =LIST PRICE * (1 - DISCOUNT/100)
                    worksheet[final_price_cell] = f"={list_price_cell}*(1-{discount_cell}/100)"

                    # Formula for TOTAL UNIT PRICE: =FINAL PRICE * QUANTITY
                    worksheet[total_unit_price_cell] = f"={final_price_cell}*{quantity_cell}"

                # Add total sum formula
                total_row = len(df) + 2
                worksheet[f"H{total_row}"] = "TOTAL SUM"
                worksheet[f"I{total_row}"] = f"=SUM(I2:I{total_row - 1})"

                # Apply number formatting
                for col in ['E', 'F', 'G', 'H', 'I']:  # Columns for numeric data
                    for row in range(2, total_row + 1):
                        cell = worksheet[f"{col}{row}"]
                        cell.number_format = '0.00'

            # Rewind the buffer
            output.seek(0)

            # Create a downloadable response with Excel data
            response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response

        except Exception as e:
            # Return error as JSON response
            return JsonResponse({'error': str(e)}, status=400)

    # Return error for non-POST requests
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# Directory to store project files
STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project_data')
os.makedirs(STORAGE_DIR, exist_ok=True)

@csrf_exempt 
def save_bom(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            project_name = data.get("project_name")
            selected_items = data.get("selectedItems")
            # print(data)
            if not project_name or not selected_items:
                return JsonResponse({"error": "Project name and selected items are required."}, status=400)
            obj = ProjectDetails.objects.filter(name=project_name)

            if obj :
                return JsonResponse({"message": f"{project_name} file already exist"})

            project = ProjectDetails(name=project_name)     
            project.save()

            
            file_path = os.path.join(STORAGE_DIR,F"{project_name}.JSON")
            with open (file_path,'w') as file:
                json.dump(selected_items,file)
            return JsonResponse({"message": f"{project_name} file succesfully created"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

            
    
def fetch_project_names(request):
    if request.method == 'GET':
        try:
            # Fetch project names as a list
            project_names = list(ProjectDetails.objects.values_list('name', flat=True))
            
            # Return the project names in a JSON response
            return JsonResponse({"projects": project_names}, status=200)
        except Exception as e:
            # Return an error response in case of failure
            return JsonResponse({"error": str(e)}, status=500)
    else:
        # Handle unsupported methods
        return JsonResponse({"error": "Invalid HTTP method."}, status=405)


    
def fetch_project_data(request):
    if request.method == 'GET':
        try:
          
            project_name = request.GET.get('project_name')

            file_path =  os.path.join(STORAGE_DIR,F"{project_name}.JSON")
            # print("file path",file_path)
            if not os.path.exists(file_path):
                return JsonResponse({"message":"file not exist"})
            
            with open (file_path,'r') as file:
                file_content = json.load(file)
            # print("filecontent",file_content)

            return JsonResponse({"file_data":file_content},status =200)


        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method. Only GET is allowed."}, status=405)