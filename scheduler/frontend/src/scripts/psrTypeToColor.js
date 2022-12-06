const PSR_COLOR_MAP = Object.freeze({
  A03: {
    psrTypeName: 'Mixed',
    color: 'hsl(0,0%,50%)',
  }, // a neutral color for a mix of sources
  A04: {
    psrTypeName: 'Generation',
    color: 'hsl(0,0%,100%)',
  }, // a bright color for the total generation
  A05: {
    psrTypeName: 'Load',
    color: 'hsl(0,0%,0%)',
  }, // a dark color for the total load
  B01: {
    psrTypeName: 'Biomass',
    color: 'hsl(120,100%,25%)',
  }, // a natural color for organic matter
  B02: {
    psrTypeName: 'Fossil Brown Coal Lignite',
    color: 'hsl(30,100%,29%)',
  }, // a dark brown color for low-quality coal
  B03: {
    psrTypeName: 'Fossil Coal Derived Gas',
    color: 'hsl(0,0%,66%)',
  }, // a dark grey color for gas derived from coal
  B04: {
    psrTypeName: 'Fossil Gas',
    color: 'hsl(0,0%,83%)',
  }, // a light grey color for natural gas
  B05: {
    psrTypeName: 'Fossil Hard Coal',
    color: 'hsl(0,0%,0%)',
  }, // a black color for high-quality coal
  B06: {
    psrTypeName: 'Fossil Oil',
    color: 'hsl(240,100%,27%)',
  }, // a dark blue color for oil
  B07: {
    psrTypeName: 'Fossil Oil Shale',
    color: 'hsl(0,100%,25%)',
  }, // a dark red color for oil shale
  B08: {
    psrTypeName: 'Fossil Peat',
    color: 'hsl(25,76%,31%)',
  }, // a brown color for peat
  B09: {
    psrTypeName: 'Geothermal',
    color: 'hsl(16,100%,50%)',
  }, // a bright orange color for geothermal energy
  B10: {
    psrTypeName: 'Hydro Pumped Storage',
    color: 'hsl(180,100%,50%)',
  }, // a cyan color for pumped storage
  B11: {
    psrTypeName: 'Hydro Run Of River And Poundage',
    color: 'hsl(195,100%,50%)',
  }, // a light blue color for run-of-river and poundage
  B12: {
    psrTypeName: 'Hydro Water Reservoir',
    color: 'hsl(240,100%,50%)',
  }, // a blue color for water reservoir
  B13: {
    psrTypeName: 'Marine',
    color: 'hsl(240,100%,40%)',
  }, // a medium blue color for marine energy
  B14: {
    psrTypeName: 'Nuclear',
    color: 'hsl(51,100%,50%)',
  }, // a gold color for nuclear energy
  B15: {
    psrTypeName: 'Other Renewable',
    color: 'hsl(120,61%,50%)',
  }, // a lime green color for other renewable sources
  B16: {
    psrTypeName: 'Solar',
    color: 'hsl(60,100%,50%)',
  }, // a yellow color for solar energy
  B17: {
    psrTypeName: 'Waste',
    color: 'hsl(0,100%,50%)',
  }, // a red color for waste
  B18: {
    psrTypeName: 'Wind Offshore',
    color: 'hsl(197,71%,73%)',
  }, // a sky blue color for offshore wind
  B19: {
    psrTypeName: 'Wind Onshore',
    color: 'hsl(195,53%,79%)',
  }, // a light sky blue color for onshore wind
  B20: {
    psrTypeName: 'Other',
    color: 'hsl(0,0%,75%)',
  }, // a silver color for other sources
  B21: {
    psrTypeName: 'Ac Link',
    color: 'hsl(328,100%,54%)',
  }, // a deep pink color for AC link
  B22: {
    psrTypeName: 'Dc Link',
    color: 'hsl(300,76%,72%)',
  }, // a violet color for DC link
  B23: {
    psrTypeName: 'Substation',
    color: 'hsl(39,100%,50%)',
  }, // an orange color for substation
  B24: {
    psrTypeName: 'Transformer',
    color: 'hsl(350,100%,88%)',
  }, // a pink color for transformer
});

const PSR_COLOR_MAP_DARKER = Object.freeze(Object.keys(PSR_COLOR_MAP)
  .reduce((accumulator, key) => {
    const psrColor = PSR_COLOR_MAP[key];
    const hsl = psrColor.color.match(/hsl\((\d+),(\d+)%,(\d+)%\)/);
    const darkerHsl = `hsl(${hsl[1]},${hsl[2]}%,${hsl[3] - 5}%)`;
    accumulator[key] = {
      psrTypeName: psrColor.psrTypeName,
      color: darkerHsl,
    };
    return accumulator;
  }, {}));

export { PSR_COLOR_MAP, PSR_COLOR_MAP_DARKER };
