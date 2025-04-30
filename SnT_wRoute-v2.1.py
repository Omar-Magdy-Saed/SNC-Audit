import json
import csv
import os
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def display_intro():
    intro_message = """
       ##################################################################################################
       ############################################### Hi, ##############################################
       # This is a simple tool to create a very dettaled service list from extract Json files , Paths ###
       #  and connections , please note you need to extract Network Data file from NFM-T to be able to ##
       # get the connections.json , also the Paths can be get via Rest as below #########################
       #  https://IP:8443/oms1350/data/otn/connections/paths ############################################
       # that there is still work in progress and will be updated with more features and options in the #
       #####  future.  for futher support please conntact me on omar.mostafa_mohamed@nokia.com  or ######
       #################          omar.mostafa.saed@gmail.com       #####################################                                                       
       ##################################################################################################
       ## BIG thnaks to my friend and colleague Mostafa Elbasha for his support and help in this tool ###
       ##################################################################################################
       ### Please Remember the full path of your input files including file name itself with extension ##
       ##################################################################################################
    """
    print(intro_message)

def get_file_path(prompt):
    while True:
        file_path = input(prompt)
        if os.path.isfile(file_path):
            return file_path
        else:
            logging.error(f"Error: The file {file_path} does not exist. Please try again.")

def load_json(file_path):
    try:
        with open(file_path) as file:
            return json.load(file, strict=False)
    except json.JSONDecodeError:
        logging.error(f"Error: The file {file_path} is not a valid JSON file.")
        exit(1)

def process_services(jsonformat, jsonformat2, writer):
    total_services = len(jsonformat['Response']['All_connections'])
    with tqdm(total=total_services, desc="Processing services") as pbar:
        for service in jsonformat['Response']['All_connections']:
            for service_data in service['connectionData']:
                if service_data['SERVICERATE'] == 1:
                    con_name = service_data['CONNECTIONNAME']
                    con_alias = service_data['CONNECTIONALIAS']

                    for blop in jsonformat2['items']:
                        if blop['guiLabel'] in service_data['CONNECTIONNAME']:
                            con_anumber = blop['orderNumber']
                            con_rate = blop['effectiveRate']

                    Prot_Unprot = "Unprotected" if service_data['PROTECTIONTYPE'] == 1 else "Protected"

                    service_servers = [server['SERVERLINKNAME'] for server in service['routeData'] if server['IMMEDIATESERVER'] == "YES"]

                    if Prot_Unprot == "Unprotected":
                        process_unprotected(service_servers, jsonformat, writer, con_anumber, con_rate, con_name, con_alias)
                    else:
                        process_protected(service_servers, jsonformat, writer, con_anumber, con_rate, con_name, con_alias)

            pbar.update(1)

def process_unprotected(service_servers, jsonformat, writer, con_anumber, con_rate, con_name, con_alias):
    trail_servers_unprotected = []
    ots_unprotected = []
    for trail in service_servers:
        for trail_alldata in jsonformat['Response']['All_connections']:
            for trail_data in trail_alldata['connectionData']:
                if trail_data['CONNECTIONNAME'] == trail:
                    for trail_server in trail_alldata['routeData']:
                        if trail_server['IMMEDIATESERVER'] == "YES":
                            infrastructure = trail_server['SERVERLINKNAME']
                            trail_servers_unprotected.append(infrastructure)
    con_unprotected_route = ','.join(trail_servers_unprotected)

    for lambdax in trail_servers_unprotected:
        for lambda_alldata in jsonformat['Response']['All_connections']:
            for lambda_data in lambda_alldata['connectionData']:
                if lambda_data['CONNECTIONNAME'] == lambdax:
                    for lambda_server in lambda_alldata['routeData']:
                        if lambda_server['CONTAINERTYPE'] == "ots":
                            ots = lambda_server['SERVERLINKNAME']
                            ots_unprotected.append(ots)
    con_unprotected_ots = ','.join(ots_unprotected)
    writer.writerow([con_anumber, con_rate, con_name, con_alias, '0', '', service_servers, 'Unprotected Route',
                     con_unprotected_route, con_unprotected_ots])

def process_protected(service_servers, jsonformat, writer, con_anumber, con_rate, con_name, con_alias):
    trail_servers_service = []
    trail_servers_protection = []
    ots_service = []
    ots_protection = []
    for trail in service_servers:
        for trail_alldata in jsonformat['Response']['All_connections']:
            for trail_data in trail_alldata['connectionData']:
                if trail_data['CONNECTIONNAME'] == trail:
                    for trail_server in trail_alldata['routeData']:
                        if trail_server['IMMEDIATESERVER'] == "YES":
                            infrastructure = trail_server['SERVERLINKNAME']
                            if trail_server['ROUTEPROTECTIONTYPE'][0] == 2:
                                trail_servers_service.append(infrastructure)
                            if trail_server['ROUTEPROTECTIONTYPE'][0] == 3:
                                trail_servers_protection.append(infrastructure)

    for lambdax in trail_servers_service:
        for lambda_alldata in jsonformat['Response']['All_connections']:
            for lambda_data in lambda_alldata['connectionData']:
                if lambda_data['CONNECTIONNAME'] == lambdax:
                    for lambda_server in lambda_alldata['routeData']:
                        if lambda_server['CONTAINERTYPE'] == "ots":
                            ots = lambda_server['SERVERLINKNAME']
                            ots_service.append(ots)

    for lambdax in trail_servers_protection:
        for lambda_alldata in jsonformat['Response']['All_connections']:
            for lambda_data in lambda_alldata['connectionData']:
                if lambda_data['CONNECTIONNAME'] == lambdax:
                    for lambda_server in lambda_alldata['routeData']:
                        if lambda_server['CONTAINERTYPE'] == "ots":
                            ots = lambda_server['SERVERLINKNAME']
                            ots_protection.append(ots)

    sharedFlag = 0
    sharedOTS = []
    con_service_ots = ','.join(ots_service)
    con_protection_ots = ','.join(ots_protection)
    con_service_route = ','.join(trail_servers_service)
    con_protection_route = ','.join(trail_servers_protection)
    for server_ots in ots_service:
        if server_ots in ots_protection:
            sharedOTS.append(server_ots)
            sharedFlag = 1

    writer.writerow([con_anumber, con_rate, con_name, con_alias, sharedFlag, sharedOTS, service_servers, 'Service',
                     con_service_route, con_service_ots, 'Protection', con_protection_route,
                     con_protection_ots])

def main():
    display_intro()

    datajson = get_file_path("Enter the path for connections.json: ")
    datajson2 = get_file_path("Enter the path for paths.json: ")

    output_csv = os.path.join(os.getcwd(), 'SNC_SharedRisk_Route_Report_ODU_OTS.csv')

    jsonformat = load_json(datajson)
    jsonformat2 = load_json(datajson2)

    try:
        with open(output_csv, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Order Number', 'Rate', 'Name', 'Alias', 'Flag', 'Shared OTS', 'Servers', 'Service',
                             'Service ODU', 'Service OTS', 'Protection', 'Protetion ODU',
                             'Protection OTS'])
            process_services(jsonformat, jsonformat2, writer)
    except IOError:
        logging.error(f"Error: Unable to open or create the file {output_csv}.")
        exit(1)

    logging.info(f"The output CSV file has been saved at: {output_csv}")

# Keep the script running until Ctrl+C is pressed
    try:
        logging.info("Press Ctrl+C to exit.")
        while True:
            pass
    except KeyboardInterrupt:
        logging.info("Exiting...")

if __name__ == "__main__":
    main()