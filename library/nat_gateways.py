import boto3
import json

# Mapping of AWS region codes to Pricing API locations
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
    'sa-east-1': 'South America (Sao Paulo)',  # Removed special character
    # Add more mappings as needed
}

def get_nat_gateway_cost(region):
    client = boto3.client('pricing', region_name='us-east-1')

    location = REGION_NAME_MAPPING.get(region, None)
    if not location:
        print(f"No location mapping found for region {region}")
        return 0, 0

    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'NAT Gateway'},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
    ]

    try:
        response = client.get_products(ServiceCode='AmazonEC2', Filters=filters)
        price_list = response['PriceList']

        if not price_list:
            print(f"No pricing data found for NAT Gateways in {location}")
            return 0, 0

        # Parse the pricing information
        price_item = json.loads(price_list[0])
        terms = price_item['terms']['OnDemand']
        hourly_cost = 0
        data_transfer_cost = 0
        for term in terms.values():
            price_dimensions = term['priceDimensions']
            for dimension in price_dimensions.values():
                if dimension['unit'] == 'Hrs':
                    hourly_cost = float(dimension['pricePerUnit']['USD'])
                elif dimension['unit'] == 'GB':
                    data_transfer_cost = float(dimension['pricePerUnit']['USD'])
        return hourly_cost, data_transfer_cost
    except Exception as e:
        print(f"Error fetching price for NAT Gateways in {location}: {e}")
        # Fallback to default pricing if available
        default_pricing = {'hourly': 0.045, 'data_transfer': 0.045}  # Example fallback values
        return default_pricing['hourly'], default_pricing['data_transfer']

def calculate_nat_gateway_total_cost():
    session = boto3.Session(region_name='us-east-1')
    ec2 = session.client('ec2')

    regions = ec2.describe_regions()['Regions']
    total_cost = 0.0
    total_nat_gateways = 0

    for region in regions:
        region_name = region['RegionName']
        print(f"Checking NAT Gateways in region: {region_name}")

        ec2_region = session.client('ec2', region_name=region_name)
        try:
            nat_gateways = ec2_region.describe_nat_gateways()['NatGateways']
        except Exception as e:
            print(f"Error retrieving NAT Gateways in region {region_name}: {e}")
            continue

        hourly_cost, data_transfer_cost = get_nat_gateway_cost(region_name)

        for nat_gateway in nat_gateways:
            nat_gateway_id = nat_gateway['NatGatewayId']
            state = nat_gateway['State']
            total_nat_gateways += 1

            # Assume NAT Gateway has been running for a full month (720 hours)
            monthly_hours = 720
            nat_cost = hourly_cost * monthly_hours

            # Example data processed value in GB; replace with actual CloudWatch metric
            data_processed_gb = 100  # Replace with actual data transfer metric
            transfer_cost = data_transfer_cost * data_processed_gb

            total_nat_cost = nat_cost + transfer_cost
            total_cost += total_nat_cost

            print(f"NAT Gateway ID: {nat_gateway_id}")
            print(f"State: {state}")
            print(f"Estimated Monthly Cost: {total_nat_cost:.2f} USD")
            print("")

    print(f"Total NAT Gateways across all regions: {total_nat_gateways}")
    print(f"Total estimated cost for all NAT Gateways: {total_cost:.2f} USD")
    return f"{total_cost:.2f}"

if __name__ == "__main__":
    calculate_nat_gateway_total_cost()
