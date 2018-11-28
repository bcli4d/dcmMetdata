import pydicom

# Remove cr/lf from a string
def remove_crlf(t):
    t = t.replace(chr(10), '')
    t = t.replace(chr(13), '')
    return t


def clean_PatientAge(t):
    t = t.lstrip('0')
    t = t.rstrip('yY')
    return t

def clean_PatientSex(t):
    if t == 'U':
        t = ''
    elif t == 'Masculino':
        t = 'M'
    elif t == 'Feminino':
        t = 'F'
    return t


def clean_PatientWeight(t):
    if t != '' and float(t) == 0.0:
        t = ''
    return t

def stringifyList(args, dataElement):
    value = ""
    for d in dataElement.value:
        value += str(d) + ","
    value = value.rstrip(',')
    return value

def cleanValue(dataElement):
    value = dataElement.value

    if dataElement.VM > 1:
        value = stringifyList(args,dataElement)
    elif dataElement.VR == 'LT':
        value = remove_crlf(value)
    elif dataElement.VR == 'FL':
        value = str(value)
    elif dataElement.VR == 'FD':
        value = str(value)
    elif value == "PatientAge":
        value = clean_PatientAge(value)
    elif value == "PatientSex":
        value = clean_PatientSex(value)
    elif value == "PatientWeight":
        value = clean_PatientWeight(value)
    return value


