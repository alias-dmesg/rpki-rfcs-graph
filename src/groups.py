import os
import json

class RFCsGroups():
    def __init__(self, groups_file=None):
        if not groups_file:
            self.groups_file = "./data/rfcs_groups.json"
        else: 
            self.groups_file = groups_file

        self.groups = {}

    def get(self):
        try:
            with open(self.groups_file) as f:
                groups = json.load(f)
        except Exception:
            return False 
        return groups

        



