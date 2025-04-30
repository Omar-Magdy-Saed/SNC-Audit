import json
import csv
import os
import logging
from tqdm import tqdm
import pandas as pd
import xlsxwriter
import openpyxl
from openpyxl.styles import PatternFill, Alignment, Font
from openpyxl.formatting.rule import FormulaRule

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

def generate_excel_report(output_csv, list_of_sites):
    # Read the CSV file
    dataSource = pd.read_csv(output_csv)

    # Generate ListOfRates from the Rate column
    ListOfRates = dataSource['Rate'].unique().tolist()
    print(f"List of Rates: {ListOfRates}")

    # Prompt user for ListOfSites
    ListOfSites = list_of_sites

    # Create a new list of sites with '-' in naming
    ListOfAdjustedSites = [w.replace('_', '-') for w in ListOfSites]

    # Arrange columns as required
    df = pd.DataFrame(dataSource, columns=['Rate', 'Protection', 'Name', 'Servers', 'Service Trails', 'Service OTS',
                                           'Protetion Trails', 'Protection OTS'])

    # Replace all site names
    for z in range(len(ListOfAdjustedSites)):
        df['Name'] = df['Name'].apply(lambda x: str(x.replace(ListOfAdjustedSites[z], ListOfSites[z])))

    # Initialize values used for filtering rates column
    for x in range(len(ListOfSites)):
        for y in range(len(ListOfRates)):
            # Filter on site name and rate plus separating routes each in a line
            sh = df[df['Rate'].str.endswith(ListOfRates[y]) & df['Name'].str.contains(ListOfSites[x])]
            str_cols = ['Service Trails', 'Service OTS', 'Protetion Trails', 'Protection OTS']
            sh[str_cols] = sh[str_cols].replace(',', '\n', regex=True)
            sh['Servers'] = sh['Servers'].apply(lambda x: str(x.replace("['", "").replace("']", "").replace(',', '\n').replace("'", "")))

            # Condition to exclude empty filtered sheets
            if len(sh.index) > 0:
                # Location of output files
                PathDestinatioin = os.path.join(os.getcwd(), f'XC-report - {ListOfSites[x]}.xlsx')

                # Calculating the width for some columns
                width = sh['Name'].str.len().max()
                width2 = len('protection') + 2
                width3 = len(sh.loc[sh.Servers != '\n', 'Servers'].max())
                width4 = 66
                width5 = 122

                # Condition to add tabs in the same excel sheet
                if y == 0:
                    # Starting xlsxwriter
                    writer = pd.ExcelWriter(PathDestinatioin, engine='xlsxwriter', mode='w')
                    # Save the dataframe
                    sh.to_excel(writer, sheet_name=ListOfRates[y], index=False, header=True)
                    # Access the XlsxWriter workbook and worksheet objects from the dataframe
                    wb = writer.book
                    ws = writer.sheets[ListOfRates[y]]

                    # Header required format
                    header_format = wb.add_format({'bold': True, 'text_wrap': False, 'valign': 'top', 'fg_color': '#D7E4BC',
                                                   'border': 1})

                    # Apply this format for all columns header
                    for col_num, value in enumerate(sh.columns.values):
                        ws.write(0, col_num, value, header_format)

                    # Freezing first three headers
                    ws.freeze_panes(1, 3)

                    # Bolding Font for a specific column
                    bold_fmt = wb.add_format({'bold': True, 'valign': 'top'})

                    # Adjusting the width for some columns
                    ws.set_column(2, 2, width + 3, bold_fmt)
                    ws.set_column(1, 1, width2 - 1)

                    if width3 > 60:
                        ws.set_column(3, 3, width3 + 3)
                    else:
                        ws.set_column(3, 3, width3 + 60)

                    ws.set_column(4, 4, width4)
                    ws.set_column(5, 5, width5)
                    ws.set_column(6, 6, width4)
                    ws.set_column(7, 7, width4 + 44)

                    # Adjusting zoom for the first tab
                    ws.set_zoom(75)

                    # Applying wrap text for columns D to H
                    wrap_format = wb.add_format({'text_wrap': True, 'valign': 'top'})
                    ws.set_column('D:H', 70, wrap_format)

                    writer.save()
                    writer.close()

                else:
                    # Starting openpyxl
                    writer = pd.ExcelWriter(PathDestinatioin, engine='openpyxl', mode='a')
                    sh.to_excel(writer, sheet_name=ListOfRates[y], index=False, header=True)

                    # Call the sheet & workbook for formatting
                    wb = writer.book
                    ws = writer.sheets[ListOfRates[y]]

                    # Adjusting the width for some columns
                    ws.column_dimensions["C"].width = width + 3
                    ws.column_dimensions["B"].width = width2 - 1

                    if width3 > 60:
                        ws.column_dimensions["D"].width = width3 + 3
                    else:
                        ws.column_dimensions["D"].width = width3 + 60

                    ws.column_dimensions["E"].width = width4
                    ws.column_dimensions["F"].width = width5
                    ws.column_dimensions["G"].width = width4
                    ws.column_dimensions["H"].width = width4 + 44

                    # Freezing first three headers
                    ws.freeze_panes = ws['D2']

                    # Applying conditional formatting color
                    color_Fill = PatternFill(bgColor="D7E4BC")
                    ws.conditional_formatting.add('A1:H1', FormulaRule(formula=['ISBLANK(I1)'], stopIfTrue=True, fill=color_Fill))

                    # Bolding Font for a specific column
                    for i in range(len(sh.index)):
                        m = "C"
                        ws[m + str(i + 2)].font = Font(bold=True)

                    # Adjusting zoom for remaining tabs
                    for ws in wb.worksheets:
                        ws.sheet_view.zoomScale = 75

                    # Applying wrap text for all columns
                    for rows in ws.iter_rows():
                        for cell in rows:
                            cell.alignment = Alignment(wrap_text=True)

                    writer.save()
                    writer.close()


def main():
    display_intro()

# Prompt user for ListOfSites
    list_of_sites = input("Enter the list of sites separated by commas: ").split(',')

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

 # Generate Excel report
    generate_excel_report(output_csv, list_of_sites)

# Keep the script running until Ctrl+C is pressed
    try:
        logging.info("Press Ctrl+C to exit.")
        while True:
            pass
    except KeyboardInterrupt:
        logging.info("Exiting...")

if __name__ == "__main__":
    main()