from locad_ad_simulator.ad.claim_extractor import extract_ad_claims


def test_claim_extractor_detects_proof_and_categories():
    copy = "Cut fulfillment costs by 44% across Shopify and Amazon. Book a 15-minute fit check."
    info = extract_ad_claims(copy)
    assert "cost" in info["categories"]
    assert info["proof_signals"]["percentage"]
    assert info["cta"] is not None
