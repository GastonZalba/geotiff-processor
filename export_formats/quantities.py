import params as params

def exportQuantities(self):
    
    quantitiesPath = '{}\\{}.txt'.format(
        params.output_folder_database_mdevalues, self.outputFilename)

    print(f'-> Exporting quantities {quantitiesPath}')

    colorValues = self.colorValues
    
    quantities = []

    i = 0
    while i < len(params.styleDEM['palette']):
        # Generating a color palette merging two structures
        quantities.append(str(round(colorValues[i], 6)))
        i += 1
    
    string = f'{{{",".join(quantities)}}}'

    fileQuantities = open(quantitiesPath, 'w')
    fileQuantities.write(string)
    fileQuantities.close()
