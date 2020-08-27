from jinja2 import Environment, FileSystemLoader
from ipaddress import IPv4Network
import ipaddress
import openpyxl

wb_obj = ""


def main():
    # Open XLS file
    open_xls("B2B VPN Jinja Templates.xlsx","Data-Site Info")
    # Find ID Column
    id_column = find_column("Data-Site Info","ID")
    # Find first data column
    first_data_column = find_column("Data-Site Info","ID:5")
    # Get all variables and values from the Data sheet into a list for each column
    xls_list = get_xls_variables("Data-Site Info", id_column, first_data_column)
    # Enhance CIDR format addresses
    xls_list = enhance_cidr(xls_list)
    if xls_list:
        # Cycle through each entry in XLS list
        for x in range(0, len(xls_list)):
            # Add current entry to dictionary
            variable_dict = xls_list[x]
            # run JINJA template against dictionary
            b2b_vpn_output = run_jinja_template("b2b_vpn_asa_config_template.txt", variable_dict)
            print(b2b_vpn_output)
            write_file(b2b_vpn_output, "B2B VPN - ASA Config_" + variable_dict["CUSTOMER_NAME"] + ".txt")
            b2b_peer_review_output = run_jinja_template("b2b_vpn_peer_review_template.txt", variable_dict)
            print(b2b_peer_review_output)
            write_file(b2b_peer_review_output, "B2B VPN - ASA Config_" + variable_dict["CUSTOMER_NAME"] + "_PEER_REVIEW.txt")

    else:
        print ("\n \nScript aborted.  Please correct the issue and re-run script.")


def write_file(input_string, filename):
    file_object = open("output/" + filename, "w+")
    file_object.write(input_string)
    file_object.close()


def enhance_cidr(data_list):
    new_data_list = []
    for x in data_list:
        new_dict = {}
        for key, value in x.items():

            try:
                if is_cidr_format(value):
                    cidr_dict = convert_cidr(value, key)
                    new_dict[key] = value
                    new_dict.update(cidr_dict)

                else:
                    new_dict[key] = value
            except:
                new_dict[key] = value

        new_data_list.append(new_dict)
    return new_data_list


def get_xls_variables(tab_name, id_column, first_data_column):
    sheet_obj = wb_obj[tab_name]

    my_list = []
    for c in range(first_data_column, sheet_obj.max_column):
        if rw_cell(1,c,tab_name):
            my_dict = {}
            my_dict["ID"] = c
            for i in range(1,sheet_obj.max_row + 1):
                #print (rw_cell(i,id_column,tab_name))
                variable_name = rw_cell(i,id_column,tab_name)
                if variable_name:
                    if left(variable_name, 3) == "DD:":
                        cell_value = rw_cell(i, c, tab_name)
                        if cell_value:
                            my_dict[variable_name.split(":")[1]] = cell_value
            my_list.append(my_dict)
    return my_list


def run_jinja_template(jinja_file, variable_dict):
    # This line uses the current directory
    file_loader = FileSystemLoader('.')
    # Load the enviroment
    env = Environment(loader=file_loader)
    # Open single Jinja2 file and load as template
    template = env.get_template(jinja_file)

    # Parse template with dictionary created
    output = template.render(variable_dict)
    return output


def open_xls(xls_input_file,tab_name):
    global wb_obj
    wb_obj = openpyxl.load_workbook(xls_input_file, data_only=True)


def find_column(tab_name,value_to_look_for):
    sheet_obj = wb_obj[tab_name]
    for i in range(1,sheet_obj.max_column):
        if rw_cell(1,i,tab_name) == value_to_look_for:
            return i


def is_cidr_format(cidr_address):
    if cidr_address.find("/") > 0:
        split = cidr_address.split("/")
        try:
            result = ipaddress.ip_address(split[0])
            if 0 < int(split[1]) <= 32:
                #print("The original string was " + cidr_address + ".  IP address is: " + str(
                #    result) + " and subnet length is " + split[1])
                return True
            else:
                pass
                #print("The string " + cidr_address + " contains an invalid subnet length.  This will result in an incomplete configuration and cause the deployment to fail.  Please correct this error and resubmit.")
        except:
            # print ("The string " + cidr_address + " contains an invalid IP Address.  This will result in an incomplete configuration and cause the deployment to fail.  Please correct this error and resubmit.")
            return False
    else:
        return False


def convert_cidr(input_cidr_dictionary, output_name):
    # This module will take an input and parse it using the ipaddress module
    net = IPv4Network(input_cidr_dictionary)
    cidr_dict = {output_name + "_IP": str(net.network_address), output_name + "_NETMASK": str(net.netmask),
                 output_name + "_WILDCARD": str(net.hostmask), output_name + "_LENGTH": int(net.prefixlen)}
    return cidr_dict


def rw_cell(row, column, sheet, write=False, value=""):
    global wb_obj
    sheet = wb_obj[sheet]
    if sheet == "":
        return
    if write is False:
        value = sheet.cell(row=row, column=column).value
        return value
    elif write is True:
        sheet.cell(row=row, column=column).value = value


def left(input_string, amount):
    return input_string[:amount]


def right(input_string, amount):
    return input_string[-amount:]


def mid(input_string, offset, amount):
    return input_string[offset:offset+amount]


main()
