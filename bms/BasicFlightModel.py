import re


class BasicFlightModel:
    class AerodataOptions:
        def __init__(self):
            self.advanced_tef = False
            self.lef_included_in_cl = False

    def __init__(self):
        self.aerodata_options = BasicFlightModel.AerodataOptions()

        self.mach_breakpoints = []
        self.alpha_breakpoints = []
        self.cl = []
        self.cd = []
        self.cy = []
        self.cl_mul = 1.0
        self.cd_mul = 1.0
        self.cy_mul = 1.0

        self.tef_mach_breakpoints = []
        self.tef_alpha_breakpoints = []
        self.tef_cl = []
        self.tef_cd = []

        self._original_content = None

    def get_multiplied_cl(self):
        return [i * self.cl_mul for i in self.cl]

    def get_multiplied_cd(self):
        return [i * self.cd_mul for i in self.cd]

    def get_multiplied_cy(self):
        return [i * self.cy_mul for i in self.cy]

    def add_new_mach_breakpoint(self, mach_num):
        def find_new_index():
            length = len(self.mach_breakpoints)
            for i in range(length):
                curr_value = self.mach_breakpoints[i]
                if curr_value == mach_num:
                    return None
                elif mach_num < curr_value:
                    return i

            return length

        def calculate_new_value(new_index, mach_num, data):
            mbps = self.mach_breakpoints
            length = len(self.alpha_breakpoints)
            length_mbps = len(mbps)

            if length_mbps == 0:
                new_list = []
                for i in range(length):
                    new_list.append(0.0)
                data.append(new_list)
            elif length_mbps == 1:
                new_list = []
                for i in range(length):
                    new_list.append(data[0][i])
                data.append(new_list)
            else:
                if new_index == 0:
                    new_list = []
                    for i in range(length):
                        slope = (data[1][i] - data[0][i]) / (mbps[1] - mbps[0])
                        dist = mbps[0] - mach_num
                        value = data[0][i] + slope * dist
                        new_list.append(value)
                    data.insert(new_index, new_list)
                elif new_index == length_mbps:
                    last_index = length_mbps - 1
                    new_list = []
                    for i in range(length):
                        slope = (data[last_index][i] - data[last_index - 1][i]) / (
                            mbps[last_index] - mbps[last_index - 1])
                        dist = mach_num - mbps[last_index]
                        value = data[last_index][i] + slope * dist
                        new_list.append(value)
                    data.insert(new_index, new_list)
                else:
                    new_list = []
                    for i in range(length):
                        slope = (data[new_index][i] - data[new_index - 1][i]) / (mbps[new_index] - mbps[new_index - 1])
                        dist = mach_num - mbps[new_index - 1]
                        value = data[new_index - 1][i] + slope * dist
                        new_list.append(value)
                    data.insert(new_index, new_list)

        new_index = find_new_index()
        if new_index is None:
            return

        self.mach_breakpoints.insert(new_index, mach_num)

        calculate_new_value(new_index, mach_num, self.cl)
        calculate_new_value(new_index, mach_num, self.cd)
        calculate_new_value(new_index, mach_num, self.cy)


def load_dat(filename):
    return _Loader().load_dat(filename)


class _Loader:
    def __init__(self):
        self._offset = 0
        self._data = []

    def load_dat(self, filename):
        fm = BasicFlightModel()

        raw_data = _read_file(filename)
        fm._original_content = raw_data
        serialized_data = self._remove_comments(raw_data)
        serialized_data = self._remove_whitespaces(serialized_data)
        self._data = serialized_data.split(' ')

        self._offset = self._find_basic_aero_coeffs_offset()
        result = self._read_basic_aerodynamic_coefficients()

        fm.mach_breakpoints = result['mach_breakpoints']
        fm.alpha_breakpoints = result['alpha_breakpoints']
        fm.cl = result['CL']
        fm.cd = result['CD']
        fm.cy = result['CY']
        fm.cl_mul = result['CL_mul']
        fm.cd_mul = result['CD_mul']
        fm.cy_mul = result['CY_mul']
        fm.aerodata_options = result['aerodata_options']

        if fm.aerodata_options.advanced_tef:
            tef_result = self._read_advanced_tef()

            fm.tef_mach_breakpoints = tef_result['mach_breakpoints']
            fm.tef_alpha_breakpoints = tef_result['alpha_breakpoints']
            fm.tef_cl = tef_result['CL']
            fm.tef_cd = tef_result['CD']

        return fm

    @staticmethod
    def _remove_comments(data):
        result = ""
        pos = 0
        length_of_data = len(data)
        while pos < length_of_data:
            eol_pos = data.find("\n", pos, length_of_data)
            if eol_pos == -1:
                break

            hash_pos = data.find("#", pos, eol_pos)
            if hash_pos == pos:
                pos = eol_pos + 1
                continue

            if hash_pos == -1:
                result = result + data[pos:eol_pos] + ' '
            else:
                result = result + data[pos:hash_pos] + ' '

            pos = eol_pos + 1

        return result

    @staticmethod
    def _remove_whitespaces(data):
        result = re.sub(' +', ' ', data)
        result = re.sub('\t+', ' ', result)
        if result[0] == ' ':
            return result[1:]

        return result

    def _read_int(self):
        value = int(float(self._data[self._offset]))
        self._offset = self._offset + 1

        return value

    def _read_float(self):
        value = float(self._data[self._offset])
        self._offset = self._offset + 1

        return value

    def _read_string(self):
        value = self._data[self._offset]
        self._offset = self._offset + 1

        return value

    def _read_array(self):
        num = self._read_int()
        array = []

        for i in range(num):
            array.append(float(self._read_float()))

        return num, array

    def _read_table(self, num_row, num_column, read_mul=True):
        table_multiplier = 1.0
        if read_mul:
            table_multiplier = self._read_float()

        table = []
        for i in range(num_row):
            row = []
            for j in range(num_column):
                row.append(self._read_float())
            table.append(row)

        return table_multiplier, table

    def _find_basic_aero_coeffs_offset(self):
        c_gear_offset = 13
        c_gear_columns = 4
        num_of_gears = int(float(self._data[c_gear_offset]))
        return c_gear_offset + num_of_gears * c_gear_columns + 6

    def _read_aerodata_options(self):
        options = BasicFlightModel.AerodataOptions()
        while self._data[self._offset].find(_c_aeropt_string) is not -1:
            option = self._data[self._offset + 1]
            if option == _c_aeropt_advanced_tef:
                options.advanced_tef = True
            elif option == _c_aeropt_lef_included_in_cl:
                options.lef_included_in_cl = True
            self._offset = self._offset + 2

        return options

    def _read_basic_aerodynamic_coefficients(self):
        # Aerodata options
        aerodata_options = self._read_aerodata_options()

        # Mach breakpoints
        num_of_mach_breakpoints, mach_breakpoints = self._read_array()

        # Alpha breakpoints
        num_of_alpha_breakpoints, alpha_breakpoints = self._read_array()

        # CL
        cl_table_multiplier, cl_table = self._read_table(num_of_mach_breakpoints,
                                                         num_of_alpha_breakpoints)

        # CD
        cd_table_multiplier, cd_table = self._read_table(num_of_mach_breakpoints,
                                                         num_of_alpha_breakpoints)

        # CY
        cy_table_multiplier, cy_table = self._read_table(num_of_mach_breakpoints,
                                                         num_of_alpha_breakpoints)

        return {'mach_breakpoints': mach_breakpoints, 'alpha_breakpoints': alpha_breakpoints, 'CL': cl_table,
                'CD': cd_table, 'CY': cy_table, 'CL_mul': cl_table_multiplier, 'CD_mul': cd_table_multiplier,
                'CY_mul': cy_table_multiplier, 'aerodata_options': aerodata_options}

    def _read_advanced_tef(self):
        # Mach breakpoints
        num_of_mach_breakpoints, mach_breakpoints = self._read_array()

        # Alpha breakpoints
        num_of_alpha_breakpoints, alpha_breakpoints = self._read_array()

        # CL
        cl_table_multiplier, cl_table = self._read_table(num_of_mach_breakpoints,
                                                         num_of_alpha_breakpoints, False)

        # CD
        cd_table_multiplier, cd_table = self._read_table(num_of_mach_breakpoints,
                                                         num_of_alpha_breakpoints, False)

        return {'mach_breakpoints': mach_breakpoints, 'alpha_breakpoints': alpha_breakpoints, 'CL': cl_table,
                'CD': cd_table}


def save_dat(fm, filename):
    c_max_num_per_line = 10

    def read_header_footer():
        content = fm._original_content
        header_pos = content.find("BASIC AERODYNAMIC COEFFICIENTS")
        header_pos = content.rfind("\n", 0, header_pos)
        header = content[0:header_pos + 1]

        footer_pos = content.find("End of Aero Data")
        footer_pos = content.find("\n", footer_pos)
        footer = content[footer_pos + 1:]

        return header, footer

    def ftt(value, spacing=11):
        return ('{:+' + str(spacing) + '.6f}').format(value)

    def add_sub_header(header):
        text = "#\n"
        text += "#-----------------------------------------------------\n"
        text += "#     " + header + "\n"
        text += "#-----------------------------------------------------\n"
        return text

    def add_array(array, header, num_text):
        text = add_sub_header(header)

        num_of = len(array)
        text += ftt(num_of, 0) + " # " + num_text + "\n"
        text += "#\n"
        for i in range(num_of):
            text += ftt(array[i])
            if (i + 1) % c_max_num_per_line == 0 and i != num_of - 1:
                text += "\n"

        text += "\n"

        return text

    def add_table(array, mul, row_array, header, mul_text, row_text):
        text = add_sub_header(header)

        num_of = len(array)
        if mul is not None:
            text += ftt(mul, 0) + " # " + mul_text + "\n"
        for i in range(num_of):
            text += "#\n"
            text += "# " + row_text + " " + '{:.1f}'.format(row_array[i]) + "\n"

            row = array[i]
            len_row = len(row)
            for j in range(len_row):
                text += ftt(row[j])
                if (j + 1) % c_max_num_per_line == 0 and j != len_row - 1:
                    text += "\n"
            text += "\n"

        return text

    def add_header():
        text = "#     BASIC AERODYNAMIC COEFFICIENTS\n"
        text += "#\n"
        return text

    def add_footer():
        text = "#\n"
        text += "# End of Aero Data\n"
        return text

    def add_aerodata_options(options):
        text = "# AERODATA OPTIONS MUST BE LISTED HERE\n"
        if options.advanced_tef:
            text += _c_aeropt_string + " " + _c_aeropt_advanced_tef + "\n"
        if options.lef_included_in_cl:
            text += _c_aeropt_string + " " + _c_aeropt_lef_included_in_cl + "\n"
        return text

    def add_advanced_tef():
        text = "#\n#\n# TEF PARAMETERS HERE\n#\n"
        text += add_array(fm.tef_mach_breakpoints, "TEF MACH BREAKPOINTS", "Num MACH")
        text += add_array(fm.tef_alpha_breakpoints, "TEF ALPHA BREAKPOINTS", "Num Alpha")
        text += add_table(fm.tef_cl, None, fm.tef_mach_breakpoints, "LIFT TEF COEFFICIENT  CL TEF",
                             None, "Mach")
        text += add_table(fm.tef_cd, None, fm.tef_mach_breakpoints, "DRAG TEF COEFFICIENT  CD TEF",
                             None, "Mach")
        return text

    # write_dat
    header, footer = read_header_footer()
    aerodata_options_set = fm.aerodata_options.advanced_tef or fm.aerodata_options.lef_included_in_cl

    mid_section = add_header()

    if aerodata_options_set:
        mid_section += add_aerodata_options(fm.aerodata_options)

    mid_section += add_array(fm.mach_breakpoints, "MACH BREAKPOINTS", "Num MACH")
    mid_section += add_array(fm.alpha_breakpoints, "ALPHA BREAKPOINTS", "Num Alpha")
    mid_section += add_table(fm.cl, fm.cl_mul, fm.mach_breakpoints, "LIFT COEFFICIENT  CL",
                                "Table Multiplier", "Mach")
    mid_section += add_table(fm.cd, fm.cd_mul, fm.mach_breakpoints, "DRAG COEFFICIENT  CD",
                                "Table Multiplier",
                                "Mach")
    mid_section += add_table(fm.cy, fm.cy_mul, fm.mach_breakpoints, "SIDE FORCE DERIVATIVE CY-BETA",
                                "Table Multiplier",
                                "Mach")

    if fm.aerodata_options.advanced_tef:
        mid_section += add_advanced_tef()

    mid_section += add_footer()

    new_content = header + mid_section + footer
    _write_file(filename, new_content)


def _read_file(filename):
    with open(filename, "r") as f:
        return f.read()


def _write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)


_c_aeropt_string = "aeropt"
_c_aeropt_advanced_tef = "AdvancedTEF"
_c_aeropt_lef_included_in_cl = "LefIncludedinCL"
