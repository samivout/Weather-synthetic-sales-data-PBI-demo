"""
Module for data fetching operations from web APIs.
"""

from lxml import etree
from io import BytesIO
import pandas as pd
from owslib.wfs import WebFeatureService

from synda.globals import *


def fetch_data_wfs(url: str, wfs_version: str, stored_query_id: str,  query_params: dict[str, str]) -> bytes:
    """Function for running a data fetch operation from the given URL with the given 
    parameters.

    Args:
        url (str): the target URL.
        wfs_version (str): the WFS version of the service.
        stored_query_id: (str): a stored query identifier of the API. Check from service provider's docs.
        query_params (dict[str, str]): a dictionary of the query parameters. Check accepted params
            from service provider's docs.

    Returns:
        The response as bytes.
    """

    wfs = WebFeatureService(url=url, version=wfs_version)
    response = wfs.getfeature(typename=[], storedQueryID=stored_query_id, storedQueryParams=query_params)

    return response.read()


def parse_fmi_xml(xml_content) -> pd.DataFrame:
    """Utility function for parsing the xml content retrieved from FMI's API into a Pandas dataframe.

    Args:
        xml_content (_type_): the retrieved xml content.

    Returns:
        pd.DataFrame: the parsed dataframe.
    """
    tree = etree.parse(BytesIO(xml_content))
    ns = {
        'wfs': 'http://www.opengis.net/wfs/2.0',
        'omso': 'http://inspire.ec.europa.eu/schemas/omso/3.0',
        'wml2': 'http://www.opengis.net/waterml/2.0'
    }
    
    all_data = []
    
    # Iterate over each member (each parameter series)
    for member in tree.findall('.//wfs:member', ns):

        obs = member.find('.//omso:PointTimeSeriesObservation', ns)
        param_elem = obs.find('.//om:observedProperty', {'om': 'http://www.opengis.net/om/2.0'})
        
        if param_elem is not None:
            # Extract parameter name from the URL
            param_name = param_elem.attrib.get('{http://www.w3.org/1999/xlink}href').split('param=')[-1].split('&')[0]
        else:
            continue
        
        points = obs.findall('.//wml2:MeasurementTVP', ns)
        for point in points:
            time_elem = point.find('wml2:time', ns)
            value_elem = point.find('wml2:value', ns)
            if time_elem is not None and value_elem is not None:
                all_data.append({
                    'timestamp': time_elem.text,
                    param_name: float(value_elem.text)
                })
    
    if all_data:
        df = pd.DataFrame(all_data)
        # Merge all rows by timestamp
        df = df.groupby('timestamp').first().reset_index()  # combine columns by timestamp
        # Convert the timestamp column from string to datetime.
        df[TIMESTAMP_STR] = pd.to_datetime(df[TIMESTAMP_STR], utc=True)
        return df
    else:
        return pd.DataFrame()