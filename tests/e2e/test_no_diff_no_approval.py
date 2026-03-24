from integration.patch_executor import apply_plan

def test_no_edits_rejected(tmp_path):
    result = apply_plan({"edits": []}, str(tmp_path))
    assert result["success"] is False
    assert result["reason"] == "no_edits"
