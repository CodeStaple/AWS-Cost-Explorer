import boto3
import json

# Mapping of AWS region codes
REGION_NAME_MAPPING = {
    'us-east-1': 'US East (N. Virginia)',
    'us-east-2': 'US East (Ohio)',
    'us-west-1': 'US West (N. California)',
    'us-west-2': 'US West (Oregon)',
    'ca-central-1': 'Canada (Central)',
    'eu-central-1': 'EU (Frankfurt)',
    'eu-west-1': 'EU (Ireland)',
    'eu-west-2': 'EU (London)',
    'eu-west-3': 'EU (Paris)',
    'eu-north-1': 'EU (Stockholm)',
    'ap-northeast-1': 'Asia Pacific (Tokyo)',
    'ap-northeast-2': 'Asia Pacific (Seoul)',
    'ap-northeast-3': 'Asia Pacific (Osaka-Local)',
    'ap-southeast-1': 'Asia Pacific (Singapore)',
    'ap-southeast-2': 'Asia Pacific (Sydney)',
    'ap-south-1': 'Asia Pacific (Mumbai)',
    'sa-east-1': 'South America (São Paulo)'
}

def get_elastic_ip_cost(region):
    client = boto3.client('pricing', region_name='us-east-1')

    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'IP Address'},
        # Removed 'location' filter to fetch more general pricing data
    ]

    try:
        response = client.get_products(ServiceCode='AmazonEC2', Filters=filters)
        price_list = response['PriceList']

        if not price_list:
            print(f"No pricing data found for Elastic IPs in {region}")
            return 0

        for price_item in price_list:
            product_data = json.loads(price_item)
            print("Product Data:", json.dumps(product_data, indent=4))  # Debug: Print product data
            terms = product_data['terms']['OnDemand']
            for term in terms.values():
                price_dimensions = term['priceDimensions']
                for dimension in price_dimensions.values():
                    if dimension['unit'] == 'Hrs':
                        price_per_hour = float(dimension['pricePerUnit']['USD'])
                        return price_per_hour
        return 0
    except Exception as e:
        print(f"Error fetching price for Elastic IPs: {e}")
        return 0

if __name__ == "__main__":
    # Test for a specific region
    cost = get_elastic_ip_cost('us-east-1')
    print(f"Elastic IP cost in us-east-1: {cost:.5f} USD per hour")
