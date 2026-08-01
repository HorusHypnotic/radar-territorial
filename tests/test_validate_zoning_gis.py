from scripts.validate_zoning_gis import EXPECTED_IDS, validate_document

def document():
    features=[]
    for index,zone_id in enumerate(sorted(EXPECTED_IDS)):
        west=-51+index*.02;ring=[[west,-8],[west+.01,-8],[west+.01,-7.99],[west,-8]]
        features.append({"type":"Feature","properties":{"id":zone_id,"vertex_count":3},"geometry":{"type":"Polygon","coordinates":[ring]}})
    return {"type":"FeatureCollection","features":features}

def test_validates_coverage_vertices_and_projected_area():
    result=validate_document(document(),b"source")
    assert result["summary"]=={"features":8,"valid":8,"invalid":0,"vertices":24,"overlaps":0,"errors":0}
    assert all(item["area_m2"]>0 for item in result["features"])
    assert len(result["metadata"]["source_sha256"])==64

def test_reports_open_ring_and_missing_zone():
    payload=document();payload["features"].pop();payload["features"][0]["geometry"]["coordinates"][0][-1]=[-50,-7];result=validate_document(payload)
    assert result["summary"]["errors"]>=2
    assert {error["type"] for error in result["errors"]}>={"coverage","geometry","ring"}
