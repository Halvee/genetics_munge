
class VcfSite(object):
    def __init__(self, data_list):
        self.chrom = data_list[0]
        self.pos = int(data_list[1])
        self.id = data_list[2]
        self.ref = data_list[3]
        self.alt = data_list[4]

class VcfVariant(VcfSite):
    def __init__(self, data_list):
        VcfSite.__init__(self, data_list)
        self.qual = float(data_list[5])
        self.filter = data_list[6]
        self.info = data_list[7]
        self.info_dict = load_key_val(self.info,sep=";",subsep="=")
        self.info_list = list(self.info_dict.keys())
        self.info_list.sort()

class VcfGts(VcfVariant):
    def __init__(self, data_list, sample_list,
                 gt_param_delim=":"):
        VcfVariant.__init__(self, data_list)
        self.gt_param_delim=gt_param_delim
        self.format = data_list[8].split(self.gt_param_delim)
        self.sample_gts = data_list[9:]
        self.gts = {}
        self.load_sample_gts(sample_list)

    def load_sample_gts(self, sample_list):
        for i in range(len(sample_list)):
            sample_i = sample_list[i]
            self.gts[sample_i] = {}
            sample_i_vals = self.sample_gts[i].split(self.gt_param_delim)
            for j in range(len(self.format)):
                format_j = self.format[j]
                self.gts[sample_i][format_j] = sample_i_vals[j]
        return self

    def get_sample_rows(self, metainfo_lists, sample_list):
        sample_rows = []
        var_row = [self.chrom, self.pos, 
                   self.id, self.ref, self.alt,
                   self.qual, self.filter]
        for col_name in metainfo_lists["INFO"]:
            if col_name not in self.info_list:
                var_row.append("0")
            else:
                var_row.append(self.info_dict[col_name])
        sample_rows = []
        for sampleid in sample_list:
            sample_row = var_row
            for col_name in metainfo_lists["FORMAT"]:
                if col_name not in self.gts[sampleid]:
                    sample_row.append("0")
                else:
                    sample_row.append(self.gts[sampleid][col_name])
            sample_rows.append(sample_row)

        return sample_rows


class VcfReader(object):
    def __init__(self, vcf_fh, delim="\t"):
        self.vcf_fh = vcf_fh
        self.delim = delim
        self.metainfo = {}
        self.vcf_header = []
        self.metainfo_lists = {"INFO":[],"FORMAT":[]}
        self.sample_list = []
        self.vcf_entry = None
        self.linenum = 0
        pass

    def load_metadata(self, line):
        info_start = line.find("<")
        info_end = line.find(">")
        metainfo_classif_end=line.find("=")
        metainfo_classif = line[:metainfo_classif_end]
        if metainfo_classif not in ("INFO","FORMAT"): 
            return self
        info = line[(info_start+1):info_end]
        keyval = load_key_val(info, sep=",", subsep="=")  
        if "ID" in keyval:
            if metainfo_classif not in self.metainfo:
                self.metainfo[metainfo_classif] = []
            self.metainfo[metainfo_classif].append(keyval)
            self.metainfo_lists[metainfo_classif].append(keyval["ID"])
        return self

    def load_header(self, line):
        self.vcf_header.extend(line.rstrip().split(self.delim))
        if len(self.vcf_header) > 9:
            self.sample_list = self.vcf_header[9:]
        return self

    def next_line(self):
        line = self.vcf_fh.readline()
        line = line.rstrip()
        if line == "":
            return self,3
        elif line[:2] == "##":
            self.load_metadata(line[2:])
            return self,0
        elif line[:1] == "#":
            self.load_header(line[1:])
            return self,1
        else:
            data = line.rstrip().split(self.delim)
            if len(data) > 0:
                self.vcf_entry = VcfGts(data, self.sample_list)
            elif len(data) > 5:
                self.vcf_entry = VcfVariant(data)
            else:
                self.vcf_entry = VcfSite(data)
            return self,2

def load_key_val(keyval_str, sep=";", subsep="="):
    keyval = {}
    keyval_list = keyval_str.split(sep)
    for keyval_i in keyval_list:
        try:
            (key,val)=keyval_i.split(subsep)
            keyval[key] = val
        except:
            keyval[keyval_i] = 1
    return keyval