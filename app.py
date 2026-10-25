from flask import Flask, render_template, request, jsonify
from bloom_filter import BloomFilter
import time

app = Flask(__name__)

# Starter configuration: 10,000 expected items, target false-positive rate ~1%.
bloom = BloomFilter(expected_items=10_000, false_positive_rate=0.01)
inserted_count = 0
checks_count = 0

# Sample data for the live demo. These are the only elements initially inserted.
SAMPLE_ITEMS = [
    "apple", "banana", "mango", "orange", "grapes",
    "pranavi123", "student001", "user2026", "neo4j", "bloomfilter"
]
for item in SAMPLE_ITEMS:
    bloom.add(item)
inserted_count = len(SAMPLE_ITEMS)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/stats")
def stats():
    return jsonify({
        "inserted_count": inserted_count,
        "checks_count": checks_count,
        "filter_size_bits": bloom.size,
        "hash_count": bloom.hash_count,
        "estimated_false_positive_rate": round(bloom.estimated_false_positive_rate(inserted_count) * 100, 4),
        "bit_array": bloom.bit_array_as_list()
    })


@app.post("/api/insert")
def insert_item():
    global inserted_count
    data = request.get_json(silent=True) or {}
    item = str(data.get("element", "")).strip()
    if not item:
        return jsonify({"error": "Please enter an element to insert."}), 400

    started = time.perf_counter()
    positions = bloom.add(item)
    elapsed_ms = (time.perf_counter() - started) * 1000
    inserted_count += 1
    return jsonify({
        "message": "Element processed and inserted into the Bloom Filter.",
        "element": item,
        "positions": positions,
        "time_ms": round(elapsed_ms, 4),
        "stats": get_stats_data()
    })


@app.post("/api/check")
def check_item():
    global checks_count
    data = request.get_json(silent=True) or {}
    item = str(data.get("element", "")).strip()
    if not item:
        return jsonify({"error": "Please enter an element to check."}), 400

    started = time.perf_counter()
    result, positions = bloom.check(item)
    elapsed_ms = (time.perf_counter() - started) * 1000
    checks_count += 1
    return jsonify({
        "element": item,
        "result": result,
        "positions": positions,
        "time_ms": round(elapsed_ms, 4),
        "explanation": (
            "All checked bits are 1, so this element may be present. "
            "A Bloom Filter can return a false positive."
            if result == "PROBABLY_PRESENT"
            else "At least one checked bit is 0, so this element is definitely not present."
        ),
        "stats": get_stats_data()
    })


@app.post("/api/bulk-insert")
def bulk_insert():
    global inserted_count
    data = request.get_json(silent=True) or {}
    raw_items = data.get("elements", [])
    if not isinstance(raw_items, list):
        return jsonify({"error": "Elements must be sent as a list."}), 400
    items = [str(x).strip() for x in raw_items if str(x).strip()]
    if not items:
        return jsonify({"error": "Enter at least one element."}), 400

    started = time.perf_counter()
    for item in items:
        bloom.add(item)
    elapsed_ms = (time.perf_counter() - started) * 1000
    inserted_count += len(items)
    return jsonify({
        "inserted_now": len(items),
        "time_ms": round(elapsed_ms, 4),
        "stats": get_stats_data()
    })


@app.get("/api/visualize")
def visualize():
    return jsonify({
        "size": bloom.size,
        "bits": bloom.bit_array_as_list()
    })


@app.post("/api/reset")
def reset_filter():
    global bloom, inserted_count, checks_count
    bloom = BloomFilter(expected_items=10_000, false_positive_rate=0.01)
    inserted_count = 0
    checks_count = 0
    return jsonify({"message": "Bloom Filter reset.", "stats": get_stats_data()})


def get_stats_data():
    return {
        "inserted_count": inserted_count,
        "checks_count": checks_count,
        "filter_size_bits": bloom.size,
        "hash_count": bloom.hash_count,
        "estimated_false_positive_rate": round(bloom.estimated_false_positive_rate(inserted_count) * 100, 4)
    }


if __name__ == "__main__":
    app.run(debug=True)
