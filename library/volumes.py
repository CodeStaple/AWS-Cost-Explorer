import boto3

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
    'sa-east-1': 'South America (São Paulo)',
}

DEFAULT_VOLUME_PRICING = {
    'gp2': 0.10,
    'gp3': 0.08,
    'io1': 0.125,
}

def get_volume_cost(volume_type, region):
    client = boto3.client('pricing', region_name='us-east-1')

    location = REGION_NAME_MAPPING.get(region, None)
    if not location:
        print(f"No location mapping found for region {region}")
        return DEFAULT_VOLUME_PRICING.get(volume_type, 0)

    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
        {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': volume_type},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
    ]

    try:
        response = client.get_products(ServiceCode='AmazonEC2', Filters=filters)
        price_list = response['PriceList']

        if not price_list:
            print(f"No pricing data found for {volume_type} in {location}")
            return DEFAULT_VOLUME_PRICING.get(volume_type, 0)

        price_item = eval(price_list[0])
        terms = price_item['terms']['OnDemand']
        for term in terms.values():
            price_dimensions = term['priceDimensions']
            for dimension in price_dimensions.values():
                price_per_gb = float(dimension['pricePerUnit']['USD'])
                return price_per_gb
    except Exception as e:
        print(f"Error fetching price for {volume_type} in {location}: {e}")
        return DEFAULT_VOLUME_PRICING.get(volume_type, 0)

def calculate_volume_total_cost():
    session = boto3.Session(region_name='us-east-1')
    ec2 = session.client('ec2')

    regions = ec2.describe_regions()['Regions']
    total_cost = 0.0

    for region in regions:
        region_name = region['RegionName']
        print(f"Checking volumes in region: {region_name}")

        ec2_region = session.client('ec2', region_name=region_name)
        try:
            volumes = ec2_region.describe_volumes()
        except Exception as e:
            print(f"Error retrieving volumes in region {region_name}: {e}")
            continue

        for volume in volumes['Volumes']:
            volume_id = volume['VolumeId']
            volume_type = volume['VolumeType']
            size_gb = volume['Size']

            cost_per_gb = get_volume_cost(volume_type, region_name)
            volume_cost = cost_per_gb * size_gb
            total_cost += volume_cost

            print(f"Volume {volume_id} in {region_name} ({volume_type}) costs {volume_cost:.2f} per month for {size_gb} GB")

    print(f"Total estimated EBS volume cost for all regions: {total_cost:.2f}")
    return f"{total_cost:.2f}"
