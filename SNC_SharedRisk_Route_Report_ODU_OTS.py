import json
import csv

datajson = 'connections.json'
datajson2 = 'paths.json'
with open(datajson) as datajson_opened:
    x = datajson_opened.read()
    jsonformat = json.loads(x, strict=False)
with open(datajson2) as datajson_opened2:
    x2 = datajson_opened2.read()
    jsonformat2 = json.loads(x2, strict=False)

file = open('SNC_SharedRisk_Route_Report_ODU_OTS.csv', mode='w', encoding='utf-8', newline='')
writer = csv.writer(file)
writer.writerow(['Order Number', 'Rate', 'Name', 'Alias', 'Flag', 'Shared OTS', 'Servers', 'Service',
                 'Service ODU', 'Service OTS', 'Protection', 'Protetion ODU',
                 'Protection OTS'])
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

file.close()
