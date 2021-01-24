import json, os, shutil, re, sys
import urllib.request
import requests
import time
import argparse

from summaries import RFCsSummaries
from groups import RFCsGroups

# Adapted from https://github.com/AndreaOlivieri/rfc2json.git
__COMPLETE_REGEX__ = r"\n(\d{4})\s(?:(Not Issued)|(?:((?:.|\s)+?(?=\.\s*\(Format))(?:\.\s*\((Format[^\)]*)\))?\s*(?:\((Obsoletes[^\)]*)\))?\s*(?:\((Obsoleted\s*by[^\)]*)\))?\s*(?:\((Updates[^\)]*)\))?\s*(?:\((Updated\s*by[^\)]*)\))?\s*(?:\((Also[^\)]*)\))?\s*(?:\((Status[^\)]*)\))?\s*(?:\((DOI[^\)]*)\))?))"
__DATE_REGEX__     = r"(?:(January|February|March|April|May|June|July|August|September|October|November|December)\s*(\d{4}))"
__FORMAT_REGEX__   = r"Format:?\s*(.*)"
__ALSO_FYI_REGEX__ = r"Also:?\s*(.*)"
__STATUS_REGEX__   = r"Status:?\s*(.*)"
__DOI_REGEX__      = r"DOI:?\s*(.*)"
__AUTHORS_REGEX__  = r"(?:((?:[A-Z]\.)+\s[^,\.]*)[,\.]\s?)+?"
__RFC_REGEX__      = r"\s?(?:([A-Z0-9]{4,})(?:,\s)?)+?"


class RFCsGraph():
    def __init__(self, rpki_rfcs_file, rfcs_index_file=None, templates_path=None, summaries_result_file=None, groups_file=None, graph_file=None):
        self.summaries = {}
        self.groups = {}
        self.rpki_rfcs = set()
        self.__RFC_INDEX_URL__ = "https://www.rfc-editor.org/rfc/rfc-index.txt"   

        if not templates_path:
            self.summaries_folder = "./summaries"
        else:
            self.summaries_folder = templates_path
        
        if not summaries_result_file:
            self.summaries_filename = "./data/rfcs_summaries.json"
        else:
            self.summaries_filename = summaries_result_file

        if not groups_file:
            self.groups_file = "./data/rfcs_groups.json"
        else: 
            self.groups_file = groups_file

        self.rpki_rfcs_file = rpki_rfcs_file

        if not rfcs_index_file:
            self.rfcs_index_file = "./data/rfc-index.txt"
        else:
            self.rfcs_index_file = rfcs_index_file

        self.rfcs_json_obj = {}
        self.d3js_data = []

        if not graph_file:
            self.graph_file = "./data/rfcs_data.json"
        else:
            self.graph_file = graph_file

    def get_rpki_rfcs(self, filename):
        result = set()
        try:
            with open(filename) as f:
                for line in f:
                    result.add(line.rstrip())
        except:
            return False
        return sorted([int(i) for i in result])

    def get_rfcs_index(self, rfcs_index_file):
        try:
            INTERVAL= 4
            INTERVAL_TIMESTAMP = INTERVAL * 60 * 60
            now = time.time()
            if not os.path.isfile(rfcs_index_file):
                r = requests.get(self.__RFC_INDEX_URL__)
                with open(rfcs_index_file, 'wb') as f:
                    f.write(r.content)
            else:
                stat = os.stat(rfcs_index_file)
                if now > (stat.st_mtime + INTERVAL_TIMESTAMP):
                    r = requests.get(self.__RFC_INDEX_URL__)
                    with open(rfcs_index_file, 'wb') as f:
                        f.write(r.content)
        except:
            return False 
        return rfcs_index_file

    def clean_text(self, text):
        return re.sub('\s+', ' ', text).strip()

    def clear_rfc(self, rfc_list):
        rfcs = []
        for rfc in rfc_list:
            if (rfc.startswith("RFC")):
                rfcs.append(rfc)
        return rfcs

    # Adapted from https://github.com/AndreaOlivieri/rfc2json.git         
    def parse_rfc_meta(self, match, rfc_number, json_obj):
        if re.search("Not Issued", match[1]):
            json_obj[rfc_number] = "Not Issued"
        else:
            json_sub_obj = {}
            title_authours_date = self.clean_text(match[2])
            authors = re.findall(__AUTHORS_REGEX__, title_authours_date)
            title = re.sub(__AUTHORS_REGEX__, '', title_authours_date, re.MULTILINE | re.UNICODE | re.DOTALL)
            json_sub_obj["authors"] = authors
            date = re.findall(__DATE_REGEX__, title_authours_date)[0]
            month = date[0]
            year = date[1]
            json_sub_obj["title"] = title.replace(". "+month+" "+year, "")
            json_sub_obj["issue_data"] = {
                "month": month,
                "year": year
            }

            if match[3]!="": json_sub_obj["format"]       = re.findall(__FORMAT_REGEX__,   self.clean_text(match[3]))[0]
            if match[4]!="": json_sub_obj["obsolets"]     = self.clear_rfc(re.findall(__RFC_REGEX__, self.clean_text(match[4])))    
            if match[5]!="": json_sub_obj["obsoleted_by"] = self.clear_rfc(re.findall(__RFC_REGEX__, self.clean_text(match[5])))    
            if match[6]!="": json_sub_obj["updates"]      = self.clear_rfc(re.findall(__RFC_REGEX__, self.clean_text(match[6])))    
            if match[7]!="": json_sub_obj["updated_by"]   = self.clear_rfc(re.findall(__RFC_REGEX__, self.clean_text(match[7])))   
            if match[8]!="": json_sub_obj["also_fyi"]     = re.findall(__ALSO_FYI_REGEX__, self.clean_text(match[8]))[0]
            if match[9]!="": json_sub_obj["status"]       = re.findall(__STATUS_REGEX__,   self.clean_text(match[9]))[0]
            if match[10]!="": json_sub_obj["doi"]          = re.findall(__DOI_REGEX__,     self.clean_text(match[10]))[0]
            json_obj[rfc_number] = json_sub_obj


    def rfcs_json_data(self):
        rfc_index_text = open(self.rfcs_index_file).read()
        rfcs_json_obj = {}
        matches = re.findall(__COMPLETE_REGEX__, rfc_index_text)
        for match in matches:
            rfc_number = match[0]
            self.parse_rfc_meta(match, rfc_number, rfcs_json_obj)
        return rfcs_json_obj

    def rfcs_name_category(self, data):
        categories = {}
        rfcs_map = {}
        for k,v in data.items():
            if v == 'Not Issued':
                continue
            status = v['status']
            caterogy_id = "_".join(status.split(" "))
            # Special case
            if int(k) == 4271:
                caterogy_id = "PROPOSED_STANDARD"

            if 'STANDARD' in caterogy_id:
                caterogy_id = "STANDARD"
            elif 'BEST' in caterogy_id:
                caterogy_id = "BCP"
            else:
                caterogy_id = caterogy_id

            if caterogy_id not in categories.keys():
                categories[caterogy_id] = [k]
            else:
                categories[caterogy_id].append(k)
            
            rfcs_map['RFC'+str(k)] = "RFCS." + str(caterogy_id) + "." + 'RFC'+str(k)
        return categories, rfcs_map


    def add_param_to_graph(self, elements, rfc_list, extended_rfcs, rfcs_groups, summaries):
        from_set = set()
        to_set = set()
        for elm in elements:
            from_set.add(elm['from'])
            to_set.add(elm['to'])
  

        for elm in elements:
            tmp = elm['from'].split(".")[-1].strip('RFC')
            rfc_content = None 
            if tmp in summaries.keys():
                rfc_content = "".join(summaries[tmp])
            if 'color' not in elm.keys(): 
                if int(tmp) in rfc_list:
                    if str(tmp) in summaries.keys():
                        elm['color'] = '#ffc107'
                        elm['summary'] = rfc_content
                    else:
                        elm['color'] = 'blue'
                        elm['summary'] = rfc_content
                else:
                    elm['color'] = 'grey'
                    elm['summary'] = rfc_content

        for elm in extended_rfcs:
            tmp = elm.split(".")[-1].strip('RFC')
            rfc_content = None 
            if tmp in summaries.keys():
                rfc_content = "".join(summaries[tmp])
            if elm in to_set:
                if int(tmp) in rfc_list:
                    if str(tmp) in summaries.keys():
                        color = '#ffc107'
                    else:
                        color = "blue"
                else:
                    color = "grey"
                
                elm_data = { 
                'from': elm, 
                'to': None,
                'kind': None,
                'color': color,
                'summary': rfc_content,
                'group': rfcs_groups[elm.split(".")[-1]]
                }

            if elm not in from_set:
                if int(tmp) in rfc_list:
                    if str(tmp) in summaries.keys():
                        color = '#ffc107'
                    else:
                        color = "blue"
                else:
                    color = "grey"
                elm_data = { 
                'from': elm, 
                'to': None,
                'kind': None,
                'color': color,
                'summary': rfc_content,
                'group': rfcs_groups[elm.split(".")[-1]]
                }

                if elm_data not in elements:
                    elements.append(elm_data)

        return elements

    def add_tooltip_to_graph(self, data, elements):
        for rfc, record in data.items():
            if record != 'Not Issued':
                status = record['status']
                issue_data = record['issue_data']
                title = record['title']
                authors = record['authors']

                title_formated = ""
                title_list = title.split()
                limit = int(len(title_list)/2)
                if len(title_list) > 10:
                    title_formated += " ".join(title_list[:limit])
                    title_formated += "</br>"
                    title_formated += " ".join(title_list[limit:])
                else:
                    title_formated = title

                if int(rfc) == 4271:
                    status = "PROPOSED STANDARD"

                rfc_title = "<div>"
                rfc_title += "<strong>RFC</strong>:" + rfc+ "</br>"
                rfc_title += "<strong>Title</strong>:" + str(title_formated) + "</br>"
                rfc_title += "<strong>Category</strong>:" + status + "</br>"
                rfc_title += "<strong>Authors</strong>:"
                rfc_title += "<ul>"
                for auth in authors:
                    rfc_title += "<li>" + auth + "</li>"
                rfc_title += "</ul>" 
                rfc_title += "<strong>Issue Date</strong>:" + issue_data['month']+" " + issue_data['year'] + "</br>"
                rfc_title += "<strong>Url</strong>: https://tools.ietf.org/html/rfc" +  str(rfc)
                rfc_title += "</div>"

                for elm in elements:
                    tmp = elm['from'].split(".")[-1].strip('RFC')
                    if int(tmp) == int(rfc):
                        elm['title'] = rfc_title

        return elements

    def format_d3js_data(self, data, rfc_list, summaries, groups):
        categories, rfcs_map = self.rfcs_name_category(data)
        rfcs_groups = {y:k for k,v in groups.items() for y in v}
        elements = []
        extended_rfcs = []

        for _,rfcs in categories.items():
    
            rfcs_filtered = [x for x in rfcs if int(x) in rfc_list ]
            named_rfcs_filtered = ['RFC'+str(x) for x in rfcs_filtered ]

            for rfc in rfcs_filtered:
                record = data[rfc]

                if 'obsolets' in record:
                    for ed in record['obsolets']:
                        if ed not in named_rfcs_filtered:
                            named_rfcs_filtered.append(ed)
                        if rfc not in named_rfcs_filtered:
                            named_rfcs_filtered.append('RFC'+str(rfc))
                        current_relation = { 
                            'from': rfcs_map['RFC'+str(rfc)],
                            'to': rfcs_map[ed], 
                            'kind': 'OBSOLETE', 
                            'group': rfcs_groups['RFC'+str(rfc)]
                            }
                        if current_relation not in elements:
                            elements.append(current_relation)

                if 'obsoleted_by' in record:
                    for ed in record['obsoleted_by']:
                        if ed not in named_rfcs_filtered:
                            named_rfcs_filtered.append(ed)
                        if rfc not in named_rfcs_filtered:
                            named_rfcs_filtered.append('RFC'+str(rfc))
                        current_relation = { 
                            'from': rfcs_map[ed], 
                            'to': rfcs_map['RFC'+str(rfc)],
                            'kind': 'OBSOLETE', 
                            'group': rfcs_groups[ed]
                            }
                        if current_relation not in elements:
                            elements.append(current_relation)

                if 'updates' in record:
                    for ed in record['updates']:
                        if ed not in named_rfcs_filtered:
                            named_rfcs_filtered.append(ed)
                        if rfc not in named_rfcs_filtered:
                            named_rfcs_filtered.append('RFC'+str(rfc))
                        current_relation = { 
                            'from': rfcs_map['RFC'+str(rfc)],
                            'to': rfcs_map[ed], 
                            'kind': 'UPDATE', 
                            'group': rfcs_groups['RFC'+str(rfc)]
                            }
                        if current_relation not in elements:
                            elements.append(current_relation)

                if 'updated_by' in record:
                    for ed in record['updated_by']:
                        if ed not in named_rfcs_filtered:
                            named_rfcs_filtered.append(ed)
                        if rfc not in named_rfcs_filtered:
                            named_rfcs_filtered.append('RFC'+str(rfc))
                        current_relation = { 
                            'from': rfcs_map[ed], 
                            'to': rfcs_map['RFC'+str(rfc)],
                            'kind': 'UPDATE',
                            'group': rfcs_groups[ed]
                            }
                        if current_relation not in elements:
                            elements.append(current_relation)
            
            extended_rfcs.extend(named_rfcs_filtered)

        extended_rfcs = [rfcs_map[x] for x in set(extended_rfcs)]

        # Add color and information about new RFCs => founded following update/obsolete relationship
        elements = self.add_param_to_graph(elements, rfc_list, extended_rfcs, rfcs_groups, summaries)
        # Add title data (tooltip)
        elements = self.add_tooltip_to_graph(data, elements)

        # for k in elements:
        #     print(k['from'], k['color'], k['group'])

        return elements

    def create(self):
        try:
            # Get RPKI RFCs list
            print("#"*5 + "= Getting RPKI RFCs list =" + "#"*5)
            self.rpki_rfcs = self.get_rpki_rfcs(self.rpki_rfcs_file)
            
            # Get all RFCs from the index file
            print("#"*5 + "= Downloading RFCs Index file =" + "#"*5)
            rfcs_index_file = self.get_rfcs_index(self.rfcs_index_file)

            print("#"*5 + "= Creatin RPKI RFCs summaries =" + "#"*5)
            # Create and format summaries by reading Markdown template
            sum_info = RFCsSummaries(templates_path=self.summaries_folder, result_file=self.summaries_filename)
            self.summaries = sum_info.get()
            

            print("#"*5 + "= Getting RPKI RFCs groups =" + "#"*5)
            # read RFC groups (MUST, MAY and SHOULD)
            grp_info = RFCsGroups(groups_file=self.groups_file)
            self.groups = grp_info.get()

            print("#"*5 + "= Formating RFCs data =" + "#"*5)
            if rfcs_index_file:
                self.rfcs_json_obj = self.rfcs_json_data()
                if self.rpki_rfcs and self.rfcs_json_obj and self.summaries and self.groups:
                    self.d3js_data = self.format_d3js_data(self.rfcs_json_obj, self.rpki_rfcs, self.summaries, self.groups)
                    if self.save_graph_data(self.d3js_data):
                        print("#"*5 + "= RPKI RFCs Graph saved in file " + str(self.graph_file) +" =" + "#"*5)

        except Exception as err:
            return err
        
        return True

    def save_graph_data(self, elements):
        try:
            with open(self.graph_file, 'w') as outfile:
                json.dump(elements, outfile)
        except:
            return False 
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build RPKI RFCs graph data.')
    parser.add_argument('-r', '--rfcs', help='RPKI RFCs list (one RFC per line)', required=True)

    args = vars(parser.parse_args())

    rpki_rfcs_file_path = args['rfcs']

    graph = RFCsGraph(rpki_rfcs_file_path,
        rfcs_index_file="./data/rfc-index.txt",
        templates_path="./summaries",
        summaries_result_file="./data/rfcs_summaries.json",
        groups_file="./data/rfcs_groups.json",
        graph_file="./html/data/rfcs_data.json")

    graph.create()

    

    

