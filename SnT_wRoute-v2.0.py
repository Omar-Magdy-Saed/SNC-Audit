import json
import csv
import os
from tqdm import tqdm

# Welcome message

print (''' 
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
       ''')

# Prompt user for file locations
datajson = input("Enter the path for connections.json: ")
datajson2 = input("Enter the path for paths.json: ")

# Generate output CSV file path
output_csv = os.path.join(os.getcwd(), 'SNC_SharedRisk_Route_Report_ODU_OTS.csv')

# Function to load JSON data from a file
def load_json(file_path):
    try:
        with open(file_path) as file:
            return json.load(file, strict=False)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON file.")
        exit(1)

# Load JSON data
jsonformat = load_json(datajson)
jsonformat2 = load_json(datajson2)

#with open(datajson) as datajson_opened:
#    x = datajson_opened.read()
#    jsonformat = json.loads(x, strict=False)
#with open(datajson2) as datajson_opened2:
#    x2 = datajson_opened2.read()
#    jsonformat2 = json.loads(x2, strict=False)

# Open the output CSV file
try:
    file = open(output_csv, mode='w', encoding='utf-8', newline='')
except IOError:
    print(f"Error: Unable to open or create the file {output_csv}.")
    exit(1)

#file = open('SNC_SharedRisk_Route_Report_ODU_OTS.csv', mode='w', encoding='utf-8', newline='')

writer = csv.writer(file)
writer.writerow(['Order Number', 'Rate', 'Name', 'Alias', 'Flag', 'Shared OTS', 'Servers', 'Service',
                 'Service ODU', 'Service OTS', 'Protection', 'Protetion ODU',
                 'Protection OTS'])


# Add progress bar
total_services = len(jsonformat['Response']['All_connections'])
with tqdm(total=total_services, desc="Processing services") as pbar:
    for service in jsonformat['Response']['All_connections']:
        for service_data in service['connectionData']:
            # Filter only E2E Services
            if service_data['SERVICERATE'] == 1:
                con_name = (service_data['CONNECTIONNAME'])
                con_alias = (service_data['CONNECTIONALIAS'])

                # Get Order number from Path Connections File
                for blop in jsonformat2['items']:
                    if blop['guiLabel'] in service_data['CONNECTIONNAME']:
                        con_anumber = blop['orderNumber']
                        con_rate = blop['effectiveRate']

                # Identifies if service is Protected or Unprotected
                if service_data['PROTECTIONTYPE'] == 1:
                    Prot_Unprot = "Unprotected"
                else:
                    Prot_Unprot = "Protected"

                # Fetch Trail Layer
                service_servers = []
                for service_server in service['routeData']:
                    if service_server['IMMEDIATESERVER'] == "YES":
                        infrastructure = service_server['SERVERLINKNAME']
                        service_servers.append(infrastructure)

                # Fetch Lambda Layer
                trail_servers_unprotected = []
                ots_unprotected = []
                if Prot_Unprot == "Unprotected":
                    for trail in service_servers:
                        for trail_alldata in jsonformat['Response']['All_connections']:
                            for trail_data in trail_alldata['connectionData']:
                                if trail_data['CONNECTIONNAME'] == trail:
                                    for trail_server in trail_alldata['routeData']:
                                        if trail_server['IMMEDIATESERVER'] == "YES":
                                            infrastructure = trail_server['SERVERLINKNAME']
                                            trail_servers_unprotected.append(infrastructure)
                    con_unprotected_route = (','.join(trail_servers_unprotected))

                    for lambdax in trail_servers_unprotected:
                        for lambda_alldata in jsonformat['Response']['All_connections']:
                            for lambda_data in lambda_alldata['connectionData']:
                                if lambda_data['CONNECTIONNAME'] == lambdax:
                                    for lambda_server in lambda_alldata['routeData']:
                                        if lambda_server['CONTAINERTYPE'] == "ots":
                                            ots = lambda_server['SERVERLINKNAME']
                                            ots_unprotected.append(ots)
                    con_unprotected_ots = (','.join(ots_unprotected))
                    writer = csv.writer(file)
                    writer.writerow([con_anumber, con_rate, con_name, con_alias, '0', '', service_servers, 'Unprotected Route',
                                     con_unprotected_route, con_unprotected_ots])

                trail_servers_service = []
                trail_servers_protection = []
                ots_service = []
                ots_protection = []
                if Prot_Unprot == "Protected":
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
                    con_service_ots = (','.join(ots_service))
                    con_protection_ots = (','.join(ots_protection))
                    con_service_route = (','.join(trail_servers_service))
                    con_protection_route = (','.join(trail_servers_protection))
                    for server_ots in ots_service:
                        if server_ots in ots_protection:
                            sharedOTS.append(server_ots)
                            sharedFlag = 1

                    writer.writerow([con_anumber, con_rate, con_name, con_alias, sharedFlag, sharedOTS, service_servers, 'Service',
                                     con_service_route, con_service_ots, 'Protection', con_protection_route,
                                     con_protection_ots])
        pbar.update(1)

file.close()

# Print the location of the output file
print(f"The output CSV file has been saved at: {output_csv}")
