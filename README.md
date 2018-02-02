# Property API
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A set of services that collect parcel-level data from the [Western Pennsylvania Regional Data Center](https://wprdc.org).  
Our current instance can be found at [https://tools.wprdc.org/property-api/](https://tools.wprdc.org/property-api/)


## Services
1. [Parcels](#parcels)


### Parcels `/parcels/<parcel_id(s)>`

Paramters:
* `parcel_id(s)` - a single 16-digit Allegheny County Parcel ID, or a comma-separated list of them

Returns a json reprsentation of all data available for the queried parcel ID.  
* `results` - the combined results of querying the datasets  
  * `geo` - geojson-formated geographic representations (centroid, boundary, address point, etc) of parcel. 
  * `owner` - the name of the property owner
  * `data` - a json object keyed by dataset identifiers.  each property of the `data` object is an array of objects representing records within the dataset identified by the key.  (e.g. the property, `assessment` will have an array with one object which contains the assessment data for the parcel. `sales` may have multiple objects in its array -- one for each sale on record)
* `failed_searches` - a list of datasets in which the search failed.  (if a search of a dataset returns zero results, but otherwise didn't run into errors, it will not be listed here.  This is primarily to discern whether no data exists, or if something is broken.)
* `success` - `true` if everything went fine, `false` otherwise
* `help` - help text for help with debugging

#### Example
`GET http://tools.wprdc.org/property-api/v0/parcels/0028F00194000000`
```json
{
  "success": true,
  "help": "Data for parcels",
  "results": [
    {
      "parcel_id": "0028F00194000000",
      "geos": {
        "centroid": {
          "coordinates": [
            "-79.96195361",
            "40.43830519"
          ],
          "type": "Point"
        }
      },
      "owner": "UNIVERSITY OF PITTSBURGH OF THE COMMONWEALTH SYSTEM OF HIGHER EDUCATION",
      "data": {
        "pgh_tax_delinquency": [],
        "assessment_appeals": [],
        "pgh_city_owned_properties": [],
        "foreclosures": [],
        "pgh-tax-abatements": [],
        "assessments": [
          {
            "CARDNUMBER": null,
            "CHANGENOTICEADDRESS3": "PITTSBURGH PA  ",
            "PROPERTYFRACTION": " ",
            "HEATINGCOOLING": null,
            "CLEANGREEN": null,
            "LOCALLAND": 126300.0,
            "CDU": null,
            "BSMTGARAGE": null,
            "CDUDESC": null,
            "FAIRMARKETTOTAL": 3819300.0,
            "ALT_ID": null,
            "SCHOOLCODE": "47",
            "COUNTYLAND": 126300.0,
            "HEATINGCOOLINGDESC": null,
            "TAXYEAR": 2018.0,
            "DEEDPAGE": "48",
            "CHANGENOTICEADDRESS2": " DEPT OF PROPERTY MANAGEMENT ",
            "PROPERTYSTATE": "PA",
            "TAXCODE": "E",
            "SALEDESC": "MULTI-PARCEL SA",
            "SCHOOLDESC": "Pittsburgh",
            "BASEMENT": null,
            "FAIRMARKETBUILDING": 3693000.0,
            "EXTFINISH_DESC": null,
            "HALFBATHS": null,
            "ABATEMENTFLAG": null,
            "CHANGENOTICEADDRESS4": "15213",
            "LEGAL2": null,
            "LEGAL3": null,
            "BEDROOMS": null,
            "PREVSALEPRICE": 1.0,
            "STORIES": null,
            "CONDITION": null,
            "PROPERTYADDRESS": "FORBES AVE",
            "ROOF": null,
            "SALEPRICE": 68899.0,
            "MUNICODE": "104",
            "ROOFDESC": null,
            "NEIGHCODE": "51C34",
            "LEGAL1": "ADA P CHILDS PLAN LOT 17 PT 16 LOT 39.5X127",
            "TOTALROOMS": null,
            "FULLBATHS": null,
            "PROPERTYCITY": "PITTSBURGH",
            "STYLEDESC": null,
            "FAIRMARKETLAND": 126300.0,
            "PROPERTYZIP": "15213",
            "OWNERDESC": "CORPORATION",
            "PREVSALEDATE2": null,
            "CLASSDESC": "GOVERNMENT",
            "LOCALBUILDING": 3693000.0,
            "USEDESC": "OWNED BY COLLEGE/UNIV/ACADEMY",
            "PREVSALEPRICE2": null,
            "FIREPLACES": null,
            "ASOFDATE": "2018-02-01",
            "MUNIDESC": "4th Ward - PITTSBURGH",
            "CHANGENOTICEADDRESS1": "127  N BELLEFIELD AVE   ",
            "LOCALTOTAL": 3819300.0,
            "DEEDBOOK": "10918",
            "HOMESTEADFLAG": null,
            "FINISHEDLIVINGAREA": null,
            "EXTERIORFINISH": null,
            "YEARBLT": null,
            "PROPERTYUNIT": " ",
            "BASEMENTDESC": null,
            "GRADEDESC": null,
            "RECORDDATE": null,
            "NEIGHDESC": "PITTSBURGH URBAN",
            "PREVSALEDATE": "07-02-1986",
            "TAXSUBCODE_DESC": null,
            "FARMSTEADFLAG": null,
            "CLASS": null,
            "PROPERTYHOUSENUM": "3343",
            "USECODE": "670",
            "TAXSUBCODE": null,
            "COUNTYTOTAL": 3819300.0,
            "SALECODE": "H",
            "LOTAREA": 5080.0,
            "GRADE": null,
            "SALEDATE": "11-20-2000",
            "COUNTYEXEMPTBLDG": 0.0,
            "STYLE": null,
            "TAXDESC": "10 - Exempt",
            "OWNERCODE": "20",
            "CONDITIONDESC": null,
            "COUNTYBUILDING": 3693000.0
          }
        ],
        "centroids_and_geo_info": [
          {
            "geo_id_SenatePA": "PASEN43",
            "geo_id_blockgp": "420030000000",
            "geo_name_HousePA": "PA House District 19",
            "level_zipcode": "Zip Code",
            "GEOID10": "420030000000000",
            "geo_name_county": "Allegheny",
            "geo_name_zipcode": "15213",
            "geo_name_countycouncil": "District 10",
            "geo_id_countycouncil": "CC10",
            "Pgh_PoliceZone": "4",
            "level_blockgp": "Block Group",
            "y": "40.43830519",
            "NAME10": "Block 1000",
            "level_tract": "Census Tract",
            "geo_id_HousePA": "PAHOUSE19",
            "geo_id_zipcode": "15213",
            "level_nhood": "Neighborhood",
            "Pgh_PLI_Zone": "4",
            "Pgh_FireDistrict": "2-14",
            "level_county": "County",
            "geo_name_schooldist": "Pittsburgh SD",
            "geo_name_tract": "40900",
            "geo_id_county": "42003",
            "geo_id_nhood": "70",
            "Pgh_Ward": "4",
            "Pgh_CityCouncil2012": "6",
            "geo_name_cousub": "Pittsburgh city",
            "COUNTYFP10": "3",
            "STATEFP10": "42",
            "TRACTCE10": "40900",
            "level_SenatePA": "PA Senate",
            "x": "-79.96195361",
            "level_schooldist": "School District",
            "geo_id_schooldist": "102027451",
            "BLOCKCE10": "1000",
            "geo_id_tract": "42003040900",
            "geo_name_nhood": "South Oakland",
            "geo_name_blockgp": "Tract 040900 Block Group 1",
            "level_HousePA": "PA House",
            "geo_name_SenatePA": "PA Senate District 43",
            "level_cousub": "County Subarea",
            "geo_id_cousub": "61000",
            "level_countycouncil": "County Council",
            "Pgh_DPW_Division": "3",
            "MAPBLOCKLO": "28-F-194"
          }
        ],
        "sales": [],
        "pli_violations": [],
        "tax_liens": [],
        "pgh-treasury-sales": []
      }
    }
  ],
  "failed_searches": []
}
```

