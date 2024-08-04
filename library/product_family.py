import boto3
import json

def list_product_families(service_code='AmazonEC2'):
    client = boto3.client('pricing', region_name='us-east-1')
    product_families = set()
    next_token = None
    
    while True:
        if next_token:
            response = client.get_products(ServiceCode=service_code, NextToken=next_token)
        else:
            response = client.get_products(ServiceCode=service_code)
        
        for price_item in response['PriceList']:
            product_data = json.loads(price_item)
            product_family = product_data.get('product', {}).get('productFamily', None)
            if product_family and product_family not in product_families:
                print(f"Found product family: {product_family}")
                print(f"Product data: {product_data}")
                product_families.add(product_family)
        
        next_token = response.get('NextToken')
        if not next_token:
            break
    
    return list(product_families)

if __name__ == "__main__":
    families = list_product_families()
    for family in families:
        print(family)
