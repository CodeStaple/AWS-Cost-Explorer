import boto3
import json

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

EIP_COST_PER_HOUR = 0.005

def get_elastic_ip_cost(region):
    return EIP_COST_PER_HOUR

def calculate_elastic_ip_total_cost():
    session = boto3.Session(region_name='us-east-1')
    ec2 = session.client('ec2')

    regions = ec2.describe_regions()['Regions']
    total_cost = 0.0
    calculation = {
        "total_cost": 0.0,
        "regions": {}
    }
    for region in regions:
        region_name = region['RegionName']
        print(f"Checking Elastic IPs in region: {region_name}")

        ec2_region = session.client('ec2', region_name=region_name)
        try:
            addresses = ec2_region.describe_addresses()
        except Exception as e:
            print(f"Error retrieving Elastic IPs in region {region_name}: {e}")
            continue

        if region_name not in calculation["regions"]:
            calculation["regions"][region_name] = {"elastic_ips": []}

        cost_per_hour = get_elastic_ip_cost(region_name)

        for address in addresses['Addresses']:
            allocation_id = address.get('AllocationId', 'Unknown')
            association_id = address.get('AssociationId', None)

            monthly_cost = cost_per_hour * 24 * 30
            total_cost += monthly_cost
            status = "idle" if not association_id else "in-use"
            print(f"Elastic IP {allocation_id} ({status}) in {region_name} costs {monthly_cost:.2f} per month")
            
            calculation["regions"][region_name]["elastic_ips"].append({
                "allocation_id": allocation_id,
                "status": status,
                "monthly_cost": f"{monthly_cost:.2f}"
            })
            calculation["total_cost"] += monthly_cost

    print(f"Total estimated cost for all Elastic IPs in all regions: {total_cost:.2f}")
    print(json.dumps(calculation, indent=4))
    return f"{total_cost:.2f}"

if __name__ == "__main__":
    calculate_elastic_ip_total_cost()
