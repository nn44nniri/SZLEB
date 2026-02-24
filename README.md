# Project single-zone lumped energy balance (0D “well-mixed air”)


## Reference

Nauta, A., Han, J., Tasnim, S. H., & Lubitz, W. D. (2024).  
**A new greenhouse energy model for predicting the year-round interior microclimate of a commercial greenhouse in Ontario, Canada.**  
*Information Processing in Agriculture*, 11(3), 438–456.  
https://doi.org/10.1016/j.inpa.2023.06.002  

Received: 18 January 2022  
Revised: 8 March 2023  
Accepted: 28 June 2023  
Available online: 30 June 2023  

Publisher: China Agricultural University. Published by Elsevier B.V. on behalf of KeAi Communications Co. Ltd.  
License: CC BY-NC-ND 4.0


---

## A) Ventilation / airflow sub-model

**(1) Leakage flow factor (low wind)**

$$
f_{\text{mini}}=\frac{V\,A_{\text{vent}}}{200}\,C_D\,C_W^{0.5}\,u
$$

Variables: $f_{\text{leakage}}$ leakage flow factor; $c_{\text{leakage}}$ leakage constant; $u$ outdoor wind speed.

**(1) Leakage flow factor (higher wind)**

$$
f_{\text{leakage}}=u,c_{\text{leakage}},\quad u\ge 0.25\ \text{m s}^{-1}
$$

Variables: same as above. 

**(2) Mini-vent ventilation flow**

$$
f_{\text{mini}}=\frac{V,A_{\text{vent}}}{200},C_D,C_W^{0.5},u
$$

Variables: ($f_{\text{mini}}$) mini-vent volumetric flow; (V) vent opening \% (0–100); ($A_{\text{vent}}$) vent area; ($C_D$) discharge coefficient; ($C_W$) wind-effect coefficient; (u) wind speed. 


**(3) Latent heat exchange due to ventilation (moisture exchange)**

$$
Q_{\text{latent}}=\frac{R_a}{3600},dx,k,(v_{\text{inside}}-v_{\text{outside}})
$$

Variables: ($Q_{\text{latent}}$) latent heat flux due to air exchange; ($R_a$) air renewal rate ($h^{-1}$); (dx) air-layer thickness; (k) latent heat of condensation; (v) absolute humidity (kg $m^{-3}$). 

---

## B) Dehumidification (MRD/HRV) and evaporative cooling pad

**(4) Heat released to air by mechanical refrigeration dehumidifier (MRD)**

$$
Q_{DH}=0.9,Q_{eo}+\frac{m_{\text{water}},k}{900}\cdot\frac{1000}{0.25}\cdot\frac{1}{SA}
$$

Variables: ($Q_{DH}$) dehumidifier heat flux to air; ($Q_{eo}$) electrical energy (kWh); ($m_{\text{water}}$) water removed (kg); (k) latent heat; (SA) greenhouse surface area. 

**(5) Moisture removed by HRV per timestep**

$$
M_{\text{removed}}=(15\ \text{min})\cdot\frac{60\ \text{s}}{\text{min}}\cdot f_{HRV},(v_{out}-v_{in})
$$

Variables: ($M_{\text{removed}}$) moisture removed in the timestep (litres, per text); ($f_{HRV}$) supply airflow ($m^{3}$ $s^{-1}$); (v) absolute humidity (kg $m^{-3}$) at HRV outlet/inlet. 

**(6) Cooling-pad outlet air temperature**

$$
T_{pad}=T_{out}-g,(T_{out}-T_{out,wb})
$$

Variables: ($T_{pad}$) pad outlet temperature; ($T_{out}$) outdoor dry-bulb temp; ($T_{out,wb}$) outdoor wet-bulb temp; (g) pad efficiency. 

**(7) Wet-bulb temperature approximation**

$$
T_{out,wb}=T_{out}- atan \big(0.152,(RH_{out}+8.31)^{0.5}\big)+ atan(T_{out}+RH_{out})- atan(RH_{out}-1.68)+0.00392,RH_{out}^{1.5}, atan(0.023,RH_{out})-4.69
$$


Variables: ($T_{out,wb}$) wet-bulb temp; ($T_{out}$) dry-bulb temp; ($RH_{out}$) outdoor relative humidity (%). 

**(8) Cooling-pad efficiency definition**

$$
g=\frac{T_{out}-T_{pad}}{T_{out}-T_{out,wb}}
$$

Variables: (g) pad efficiency; temps as above. 

**(9) Sensible cooling from evaporative pad**

$$
Q_{cool}=\frac{f_{evap},c_{air},\rho_{air},MV,CP,(T_{in}-T_{pad})}{SA}
$$

Variables: ($Q_{cool}$) sensible cooling flux; ($f_{evap}$) pad ventilation flow; ($c_{air}$) air heat capacity; ($\rho_{air}$) air density; (MV) main-vent opening %; (CP) pad valve opening %; ($T_{in}$) indoor air temp; (SA) surface area. 

**(10) Absolute humidity leaving the cooling pad**

$$
v_{pad}=v_{outside}+g,(v_{sat}-v_{inside})
$$

Variables: ($v_{pad}$) humidity at pad outlet; ($v_{outside}$) outdoor absolute humidity; ($v_{sat}$) saturated humidity of outdoor air; ($v_{inside}$) indoor absolute humidity; (g) pad efficiency. 

**(11) Moisture added/removed by the cooling pad (per layer, per step)**

$$
M_{CP}=\frac{f_{evap},dt,CP,MV,(v_{inside}-v_{pad})}{SA;dx_{airlayer}}
$$

Variables: ($M_{CP}$) moisture change from pad; (dt) timestep; ($dx_{airlayer}$) air-layer thickness; others as above. 

---

## C) Psychrometrics (RH ↔ absolute humidity, saturation vapor pressure)

**(12) Absolute humidity from RH and temperature (modified ideal gas law form)**

$$
v_{outside}=\frac{e_s,(RH/100)}{T;C_{vap}}
$$

Variables: ($v_{outside}$) absolute humidity (kg $m^{-3}$); ($e_s$) saturated vapor pressure (Pa); (RH) relative humidity (%); (T) air temperature (K here); ($C_{vap}$) water-vapor gas constant/“heat capacity” term used by authors (461.5 J $kg^{-1}$ $K^{-1}$). 

**(13) Saturated vapor pressure (Magnus–Tetens)**

$$
e_s=610.94;\exp!\left(\frac{17.625,T}{243.04+T}\right)
$$

Variables: ($e_s$) saturated vapor pressure (Pa); (T) temperature (°C in this formula). 

---

## D) Plant transpiration and moisture balance

**(14) Transpiration latent heat flux**

$$
Q_{trans}=k;VEC;(e_s-e_{air})
$$

Variables: ($Q_{trans}$) transpiration heat flux; (k) latent heat term; (VEC) vapor exchange coefficient; ($e_s$) saturated vapor pressure; ($e_{air}$) air vapor pressure (authors compute from ($e_s$) and RH). 

**(15) Vapor exchange coefficient**

$$
VEC=\frac{2,c_{air},\rho_{air},LAI}{k,\gamma,(r_b+r_s)}
$$

Variables: ($c_{air}$) air heat capacity; ($\rho_{air}$) air density; (LAI) leaf area index; ($\gamma$) psychrometric constant; ($r_b$) boundary-layer resistance; ($r_s$) stomatal resistance; (k) latent heat term. 

**(16) Canopy stomatal resistance (empirical)**

$$
r_s=82+570;\exp!\left(-\frac{k_{tp},R_n}{LAI}\right)\left(1+0.023,(T-20)^2\right)
$$

Variables: ($r_s$) stomatal resistance; ($k_{tp}$) crop transpiration parameter; ($R_n$) net radiation; (LAI) leaf area index; (T) air temperature (°C). 

**(17) Change in absolute humidity in the greenhouse air (moisture budget core)**

$$
dAH=\frac{dt,(Q_{trans}-Q_{latent})}{k;dx_{airlayers}}
$$

Variables: (dAH) change in absolute humidity (kg $m^{-3}$); (dt) timestep; ($Q_{trans}$) transpiration term; ($Q_{latent}$) ventilation moisture-loss term; (k) latent heat term; ($dx_{airlayers}$) combined air-layer thickness. 

---

## E) Radiant sky temperature and sky emissivity

**(18) Radiant sky temperature (as printed; PDF parsing is cramped but structure is clear)**

$$
T_{sky}=\Big((1-f),\varepsilon_{sky},(T_{amb}+273.15)^4+f,(T_{amb}+273.15)^4\Big)^{0.25}-273.15
$$

Variables: ($T_{sky}$) radiant sky temperature (°C); (f) cloud fraction; ($\varepsilon_{sky}$) sky emissivity; ($T_{amb}$) ambient outdoor temperature (°C). 

**(19) Sky emissivity**

$$
\varepsilon_{sky}=0.736+0.00577,T_{dp}
$$

Variables: ($\varepsilon_{sky}$) sky emissivity; ($T_{dp}$) dewpoint temperature (°C). 

**(20) Dewpoint temperature from RH and ambient temperature**

$$
T_{dp}=\left(\frac{RH}{100}\right)^{1/8}\big(112+0.9,T_{amb}\big)+0.1,T_{amb}-112
$$

Variables: ($T_{dp}$) dewpoint (°C); (RH) relative humidity (%); ($T_{amb}$) ambient outdoor temperature (°C). 

---

## F) Convective heat transfer coefficients (Table 2)

**(21) Outside convection at glazing**

$$
h=7.2+3.84,u
$$

Variables: (h) convective heat transfer coefficient; (u) wind speed. 

**(22) Internal air ↔ glazing/curtain convection**

$$
h=2.21,(T_{air}-T_{cov})^{0.33}\quad \text{for }0.3 < (T_{air}-T_{cov})<13.8^\circ\text{C}
$$

Variables: (h) convection coefficient; ($T_{air}$) air temperature; ($T_{cov}$) cover temperature. 

**(23) Soil/floor ↔ air convection**

$$
h=10;\big|;T_{soil}-T_{air};\big|^{0.33}
$$

Variables: (h) convection coefficient; (T_{soil}) soil/floor temperature; (T_{air}) air temperature. 

**(24) Plant canopy ↔ air convection**

$$
h=10;LAI
$$

Variables: (h) canopy-to-air convection coefficient; (LAI) leaf area index. 

---

## G) Plant canopy radiation factors

**(25) Canopy transmissivity to solar radiation (special case of Beer’s law)**

$$
\tau_{sol,7}=(1-\alpha_{sol,7}),\exp(-k_{att},LAI)
$$

Variables: ($\tau_{sol,7}$) canopy solar transmissivity; ($\alpha_{sol,7}$) canopy solar reflectivity; ($k_{att}$) canopy attenuation coefficient; (LAI) leaf area index. 

**(26) Canopy “area factor” used for IR pathways**

$$
A_{canopy}=1-\exp(-k_{FIR},LAI)
$$

Variables: ($A_{canopy}$) plant area factor (effective emitting/absorbing area ratio); ($k_{FIR}$) IR extinction coefficient; (LAI) leaf area index. 

---

## H) Heat-transfer pathway formulas (Table 3 excerpts)

Table 3 contains **many** individual pathway equations (solar, IR, conduction, ventilation, heating). The IR terms repeatedly use the Stefan–Boltzmann form “($\sigma$ $\times$) (view/coverage factors) ($\times$) (($\varepsilon_i$ $T_i^4$ - $\varepsilon_j$ $T_j^4$))”. Examples explicitly visible in the parsed text include:  

* $(Q_{IR,7\to6}=\sigma,A_{crop},A_{canopy},(\varepsilon_7 T_7^4-\varepsilon_6 T_6^4))$ (plant ↔ potted soil) 
* $(Q_{IR,14\to13}=\sigma,A_{crop},(\varepsilon_{14} T_{14}^4-\varepsilon_{13} T_{13}^4))$ (floor ↔ bottom soil layer) 
* $(Q_{IR,7\to5}=\sigma,A_{crop},(1-s_{IR,5}-a_{IR,5}),A_{canopy},(\varepsilon_7 T_7^4-\varepsilon_5 T_5^4))$ (plant ↔ curtain) 
* $(Q_{IR,14\to5}=\sigma,(1-A_{crop}),(1-s_{IR,5}-a_{IR,5}),(\varepsilon_{14} T_{14}^4-\varepsilon_5 T_5^4))$ (ground ↔ curtain) 
* $(Q_{IR,5\to3}=\sigma,(1-s_{IR,1}-a_{IR,1}),(\varepsilon_5 T_5^4-\varepsilon_3 T_3^4))$ (curtain ↔ glazing) 
* $(Q_{IR,14\to sky})$ and $(Q_{IR,7\to sky})$ are also written explicitly with factors including ($s_{IR}$), ($A_{crop}$), ($A_{canopy}$), ($\varepsilon_{sky}$), ($T_{sky}$). 

Other non-IR pathway formulas visible in Table 3 include:
* **Ventilation sensible heat loss**

$$
Q_{vent,4\&6} = \frac{R_a}{3600} \cdot (dx_4 + dx_6) \cdot \rho_{air} \cdot c_{air} \cdot (T_6 - T_{amb})
$$

Variables : ($R_a$) air renewal rate ; ($dx_4, dx_6$) air-layer thicknesses ; ($T_6$) lower-air temperature ; ($T_{amb}$) ambient outdoor temp.

* **Ventilation sensible heat loss**

  $$
  Q_{vent,4&6}=\frac{R_a}{3600},(dx_4+dx_6),\rho_{air},c_{air},(T_6-T_{amb})
  $$
  
  Variables: ($R_a$) air renewal rate; ($dx_4,dx_6$) air-layer thicknesses; ($T_6$) lower-air temperature; ($T_{amb}$) ambient outdoor temp. 

* **HRV sensible heat transfer**
  
  $$
  Q_{HRV}=\frac{f_{HRV},\rho_{air},c_{air},(T_{out,HRV}-T_{in,HRV})}{SA}
  $$
  
  Variables: ($f_{HRV}$) HRV airflow; ($T_{out,HRV},T_{in,HRV}$) HRV outlet/inlet temps; (SA) surface area. 

* **Heating pipe convective input (upper/mid/lower)**
  
  $$
  Q_{upper,mid,lower}=\frac{F,c_{water},(T_{in}-T_{out})}{SA}
  $$

  Variables: (F) hot-water mass flow term (as used by authors); ($c_{water}$) water heat capacity; ($T_{in},T_{out}$) pipe inlet/outlet water temps; (SA) surface area. 
  
* **Conduction through soil layers**
  
  $$
  Q_{cond}=k_{soil},\frac{(T_n-T_{n-1})}{0.5,dx_n+0.5,dx_{n-1}}
  $$

  Variables: (k_{soil}) soil conductivity; (T_n,T_{n-1}) layer temperatures; (dx_n,dx_{n-1}) layer thicknesses. 
  
---

## I) Core state-space / layer temperature update equations (Appendix)

These are the **discrete-time layer temperature updates** (dT_i) (energy balance per layer). They are the “state equations” of the lumped-capacitance model.

**No curtain (27–37):**  

* **(27)**
  [
  dT_1=\frac{dt,(Q_{solrad1}+Q_{cond2\to1}-Q_{conv1\to amb}-Q_{IR1\to sky})}{c_1\rho_1 dx_1}
  ]
* **(28)**
  [
  dT_2=\frac{dt,(Q_{cond2\to1}+Q_{cond3\to2})}{c_2\rho_2 dx_2}
  ]
* **(29)**
  [
  dT_3=\frac{dt,(Q_{solradref3}+Q_{conv4\to3}+Q_{IR5\to3}+Q_{IR12\to3}-Q_{cond3\to2})}{c_3\rho_3 dx_3}
  ]
* **(30)**
  [
  dT_4=\frac{dt,(Q_{conv4\to3}+Q_{solrad4}-Q_{vent4}+0.75,Q_{upper})}{c_4\rho_4 dx_4}
  ]
* **(31)**
  [
  dT_6=\frac{dt,(Q_{solrad6}+Q_{conv7\to6}+Q_{conv8\to6}-0.5,Q_{trans7\to6}+Q_{conv14\to6}-Q_{vent6}-Q_{HRV}+Q_{mid}+0.25Q_{upper}+0.25Q_{lower}+Q_{gas}+Q_{light}-Q_{cool}+Q_{DH})}{c_6\rho_6 dx_6}
  ]
* **(32)**
  [
  dT_7=\frac{dt,(Q_{solrad7}+Q_{solradref7}-Q_{conv7\to6}-Q_{IR7\to3}+Q_{IR8\to7}-0.5Q_{trans7\to6}-Q_{IR7\to sky})}{c_7\rho_7 dx_7}
  ]
* **(33)**
  [
  dT_8=\frac{dt,(Q_{solrad8}-Q_{conv8\to6}-Q_{IR8\to7}+Q_{cond9\to8}+0.75Q_{lower})}{c_8\rho_8 dx_8}
  ]
* **(34)** (generic for multiple soil layers)
  [
  dT_i=\frac{dt,(Q_{cond,i+1\to i}-Q_{cond,i\to i-1})}{c_i\rho_i dx_i}
  ]
* **(35)**
  [
  dT_{13}=\frac{dt,(Q_{cond13\to12}+Q_{IR14\to13})}{c_{13}\rho_{13} dx_{13}}
  ]
* **(36)**
  [
  dT_{14}=\frac{dt,(Q_{solrad14}-Q_{conv14\to6}-Q_{IR14\to3}+Q_{cond15\to14}-Q_{IR14\to sky}-Q_{IR14\to13})}{c_{14}\rho_{14} dx_{14}}
  ]
* **(37)**
  [
  dT_{21}=\frac{dt,(Q_{cond21\to20})}{c_{21}\rho_{21} dx_{21}}
  ]

**Curtain deployed (38–43):** 

* **(38)**
  [
  dT_3=\frac{dt,(Q_{IR5\to3}+Q_{conv4\to3}+Q_{IR7\to3}+Q_{IR14\to3}-Q_{cond3\to2})}{c_3\rho_3 dx_3}
  ]
* **(39)**
  [
  dT_4=\frac{dt,(Q_{conv4\to3}+Q_{solrad4}-Q_{vent4}+Q_{conv5\to4})}{c_4\rho_4 dx_4}
  ]
* **(40)**
  [
  dT_5=\frac{dt,(Q_{solrad5}+Q_{solradref5}+Q_{conv6\to5}+Q_{IR7\to5}+Q_{IR14\to5}-Q_{conv5\to4}-Q_{IR5\to sky}-Q_{IR5\to3}+0.75Q_{upper})}{c_5\rho_5 dx_5}
  ]
* **(41)**
  [
  dT_6=\frac{dt,(...+Q_{conv6\to5}-Q_{cool}+Q_{DH})}{c_6\rho_6 dx_6}
  ]
  (same structure as (31) but with the added (Q_{conv6\to5}) and curtain-related pathways) 
* **(42)**
  [
  dT_7=\frac{dt,(Q_{solrad7}+Q_{solradref7}-Q_{conv7\to6}-Q_{IR7\to3}-Q_{IR7\to5}+Q_{IR8\to7}-0.5Q_{trans7\to6}-Q_{IR7\to sky})}{c_7\rho_7 dx_7}
  ]
* **(43)**
  [
  dT_{14}=\frac{dt,(Q_{solrad14}-Q_{conv14\to6}-Q_{IR14\to3}+Q_{cond15\to14}-Q_{IR14\to sky}-Q_{IR14\to13}-Q_{IR14\to5})}{c_{14}\rho_{14} dx_{14}}
  ]

**Variables (shared across Appendix equations):** (dt) timestep; (dT_i) temperature change of layer (i); (c_i,\rho_i,dx_i) heat capacity, density, thickness of layer (i); each (Q_{*}) is a heat-flux pathway term named by its physics and direction (e.g., convection, conduction, radiation, ventilation, heaters, lights, pads, dehumidifier). 


