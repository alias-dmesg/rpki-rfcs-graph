import os
import re
import json
import marko
from markdown_tree_parser.parser import parse_file



class RFCsSummaries():
    def __init__(self, templates_path=None, result_file=None):
        self.summaries = {}
        if not templates_path:
            self.summaries_folder = "./summaries"
        else:
            self.summaries_folder = templates_path
        
        if not result_file:
            self.summaries_filename = "./data/rfcs_summaries.json"
        else:
            self.summaries_filename = result_file

    def get(self):
        for root, _, files in os.walk(self.summaries_folder):
            for file in files:
                title = None 
                targets = None
                terminology = None
                text = None
                summary = []
                rfc = None

                if 'rfc' in file:
                    rfc = re.findall("\d+", file)[0]
                    if rfc:
                        filename = os.path.join(root,file)
                        out = parse_file(filename)

                        # TITLE
                        title = marko.convert(out.title)
                        title = re.sub("</?p[^>]*>", "", title)
                        
                        if out[0].text == "Content":
                            # TARGET
                            if out[0][0].text == "Targets":
                                targets = marko.convert(out[0][0].source)
                                targets = re.sub("</?p[^>]*>", "", targets)
                            # TERMINOLOGY 
                            if out[0][1].text == "Terminology":
                                terminology = marko.convert(out[0][1].source)
                                terminology = re.sub("</?ul[^>]*>", "", terminology)
                                terminology = re.sub("</?a[^>]*>", "", terminology)
                                terminology = re.sub("<li[^>]*>", "<span class='badge badge-success'>", terminology)
                                terminology = re.sub("</li[^>]*>", "</span>", terminology)
                            # TEXT 
                            if out[0][2].text == "Summary":
                                text = marko.convert(out[0][2].source)
                                text = re.sub("</?p[^>]*>", "", text)

                        if title and targets and terminology and text:
                            summary.append("<div class='card'>")
                            summary.append("<div class='card-header'>")
                            summary.append(title)
                            summary.append("</div>")
                            summary.append("<div class='card-body'>")
                            summary.append("<h5 class='card-title'>Targets: " + str(targets) + "</h5>")
                            summary.append("<h6 class='card-subtitle mb-2 text-muted'>Terminology</h6>")
                            summary.append("<p class='card-text'>")
                            summary.append(terminology)
                            summary.append("<hr/>")
                            summary.append(text)
                            summary.append("</p>")
                            summary.append("</div>")
                            summary.append("</div>")
                        
                if rfc and summary:
                    self.summaries[rfc] = summary



        if self.summaries:
            try:
                with open(self.summaries_filename, "w") as fo:
                    json.dump(self.summaries, fo)
            except Exception:
                return False
            
            return self.summaries
        
        return False



    def info(self):
        return self.summaries_filename



if __name__ == "__main__":
    sum = RFCsSummaries()
    sum.get()