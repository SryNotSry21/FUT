from __future__ import annotations

from futbot.market.prices import decode_platform_prices, merge_price_blobs, reconstruct_ids


def test_reconstruct_ids_from_deltas() -> None:
    blob = {"id0": 10, "d": [5, 2, 20]}
    assert reconstruct_ids(blob) == [10, 15, 17, 37]


def test_decode_platform_prices() -> None:
    blob = {
        "id0": 100,
        "d": [1, 1],
        "p": [5000, 0, 12000],
        "s": [0, 0, 1],
        "sbcs": {"102": 86},
    }
    prices = decode_platform_prices(blob, "ps5")
    assert prices[100].price == 5000
    assert prices[100].is_extinct is False
    assert prices[101].price is None
    assert prices[101].is_extinct is True
    assert prices[102].is_sbc is True
    assert prices[102].price is None


def test_merge_dyn_blob_with_index() -> None:
    index = {"id0": 7, "d": [3], "spp": {}, "sbcs": {}}
    dyn = {"v": 2, "p": [9000, 11000], "s": [0, 0]}
    merged = merge_price_blobs(index, dyn)
    prices = decode_platform_prices(merged, "pc")
    assert prices[7].price == 9000
    assert prices[10].price == 11000
    assert prices[10].platform == "pc"


def test_reconstruct_len_matches_ids() -> None:
    from futbot.market.futgg import reconstruct_len

    index = {"id0": 7, "d": [3, 4]}
    assert reconstruct_len(index) == 3
    assert reconstruct_len(index) == len(reconstruct_ids(index))


def test_length_mismatch_raises() -> None:
    blob = {"id0": 1, "d": [1, 1], "p": [1], "s": [0]}
    try:
        decode_platform_prices(blob, "ps5")
    except ValueError as exc:
        assert "mismatch" in str(exc)
    else:
        raise AssertionError("expected mismatch error")
