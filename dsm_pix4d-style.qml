<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.20.2-Odense" hasScaleBasedVisibilityFlag="0" minScale="1e+08" styleCategories="AllStyleCategories" maxScale="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>0</Searchable>
    <Private>0</Private>
  </flags>
  <temporal enabled="0" fetchMode="0" mode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <Option type="Map">
      <Option name="WMSBackgroundLayer" type="QString" value="false"/>
      <Option name="WMSPublishDataSourceUrl" type="QString" value="false"/>
      <Option name="embeddedWidgets/count" type="QString" value="0"/>
      <Option name="identify/format" type="QString" value="Value"/>
    </Option>
  </customproperties>
  <pipe>
    <provider>
      <resampling maxOversampling="2" enabled="false" zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer band="1" alphaBand="-1" classificationMax="35.2768526" type="singlebandpseudocolor" opacity="1" nodataColor="" classificationMin="20.9353636">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>CumulativeCut</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.001</cumulativeCutLower>
        <cumulativeCutUpper>0.96</cumulativeCutUpper>
        <stdDevFactor>2.5</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" minimumValue="20.935363599999999" clip="0" labelPrecision="6" classificationMode="1" maximumValue="35.276852599999998">
          <colorramp name="[source]" type="gradient">
            <Option type="Map">
              <Option name="color1" type="QString" value="0,0,187,255"/>
              <Option name="color2" type="QString" value="178,0,6,255"/>
              <Option name="discrete" type="QString" value="0"/>
              <Option name="rampType" type="QString" value="gradient"/>
              <Option name="stops" type="QString" value="0.0721154;81,222,222,255:0.203125;87,237,90,255:0.313702;68,236,53,255:0.603365;223,227,1,255:0.793269;255,134,2,255"/>
            </Option>
            <prop k="color1" v="0,0,187,255"/>
            <prop k="color2" v="178,0,6,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.0721154;81,222,222,255:0.203125;87,237,90,255:0.313702;68,236,53,255:0.603365;223,227,1,255:0.793269;255,134,2,255"/>
          </colorramp>
          <item color="#0000bb" label="20.935364" alpha="255" value="20.9353636"/>
          <item color="#51dede" label="21.969606" alpha="255" value="21.969605595192306"/>
          <item color="#57ed5a" label="23.848479" alpha="255" value="23.848478553125"/>
          <item color="#44ec35" label="25.434317" alpha="255" value="25.434317382278"/>
          <item color="#dfe301" label="29.588516" alpha="255" value="29.588516110485"/>
          <item color="#ff8602" label="32.312022" alpha="255" value="32.312022237541"/>
          <item color="#b20006" label="35.276853" alpha="255" value="35.2768526"/>
          <rampLegendSettings minimumLabel="" maximumLabel="" suffix="" useContinuousLegend="1" direction="0" prefix="" orientation="2">
            <numericFormat id="basic">
              <Option type="Map">
                <Option name="decimal_separator" type="QChar" value=""/>
                <Option name="decimals" type="int" value="6"/>
                <Option name="rounding_type" type="int" value="0"/>
                <Option name="show_plus" type="bool" value="false"/>
                <Option name="show_thousand_separator" type="bool" value="true"/>
                <Option name="show_trailing_zeros" type="bool" value="false"/>
                <Option name="thousand_separator" type="QChar" value=""/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast gamma="1" contrast="0" brightness="0"/>
    <huesaturation colorizeStrength="100" grayscaleMode="0" colorizeBlue="128" colorizeRed="255" saturation="0" colorizeGreen="128" colorizeOn="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
