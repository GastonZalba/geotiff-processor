import params as params

def exportQuantities(self):

    colorValues = self.colorValues
    
    quantities = []

    quantitiesPath = '{}\\{}.txt'.format(
        params.output_folder_database, self.outputFilename)

    fileQuantities = open(quantitiesPath, 'w')

    i = 0
    fileQuantities.write('{')
    while i < len(params.styleDEM['palette']):
        # Generating a color palette merging two structures
        quantities.append(str(round(colorValues[i], 6)))
        i += 1
    fileQuantities.write(",".join(quantities))
    fileQuantities.write('}')
    fileQuantities.close()
