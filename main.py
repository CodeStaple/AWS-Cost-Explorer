from library.instances import calculate_total_cost
from library.elastic_ips import calculate_elastic_ip_total_cost
from library.rdss import calculate_rds_total_cost
from library.volumes import calculate_volume_total_cost
from library.nat_gateways import calculate_nat_gateway_total_cost
from library.internet_gateway import list_internet_gateways
from library.loadbalancers import list_load_balancers

if __name__ == "__main__":
    elastic_ips = calculate_elastic_ip_total_cost()
    loadbalancers = list_load_balancers()
    volumes = calculate_volume_total_cost()
    rdss = calculate_rds_total_cost()
    nat_gateways = calculate_nat_gateway_total_cost()
    internet_gateways = list_internet_gateways()
    instances = calculate_total_cost()
    total_price = float(volumes) + float(nat_gateways) + float(internet_gateways) +float(elastic_ips) + float(instances) + float(loadbalancers)
    print(f"Total estimated cost for all resources: {float(total_price):.2f}")

    
