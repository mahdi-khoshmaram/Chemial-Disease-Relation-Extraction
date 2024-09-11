
import re
result_file = "results.pubtatur.text"
test_file = "test.PubTator_edited.txt"

def handle(file):
    with open(file, 'r') as fh:
        data = fh.read()
    pattern = "\n\n"
    docs = re.split(pattern, data)

    for doc in docs:
        if doc.strip() == '':
            docs.remove(doc)
    documents = {}
    for doc in docs:
        rels = []
        doc = doc.strip()
        # [id,text]
        split1 = doc.split('|t|')
        # id
        doc_id = split1[0].strip()
        documents[doc_id] = {}
        text =  split1[1]
        # text = [titel, rels]
        split2 = text.split('\n')
        # title
        title = split2[0].strip()
        documents[doc_id]["title"] = title
        for rel in split2[1:]:
            rels.append(rel)
        documents[doc_id]["rels"] = rels
    return documents


dic_result = handle(result_file)
dic_test = handle(test_file)
print(dic_result["24582773"]['rels'])

all = {}
for id in dic_result.keys():
    all[id] = {}
    # test
    ltest = []
    for rel in dic_test[id]['rels']:
        chemdi = rel.split('\t')
        chem = chemdi[2]
        dis = chemdi[3]
        ltest.append((chem, dis))
    all[id]['test'] = ltest

    lres = []
    for rel in dic_result[id]['rels']:
        chemdires = rel.split('\t')
        chem = chemdires[2]
        di = chemdires[3]
        if "\t" in di:
            di = ' '.join(di.split('\t'))
        lres.append((chem, di))
    all[id]['res'] = lres
    
for id in all.keys():
    print(f"{all[id]['test']}")
    print(f"{all[id]['res']}")
    print('*********************************')
print(all["24571687"])
breakpoint
tp = 0
fp = 0
fn = 0
for id in all.keys():
    resrels = all[id]['res']
    testrels = all[id]['test']
    for tuple in resrels:
        if tuple in testrels:
            tp += 1
            testrels.remove(tuple)
            continue
        if tuple not in testrels:
            fp += 1
    fn += len(testrels)
print(f"\n---------------\ntp={tp}\nfp={fp}\nfn={fn}\n---------------")

precision = tp / (tp + fp)
recall = tp / (tp + fn)
fmeasure = 2 * ((precision*recall) /(precision+recall))

print(f"\n\n\nprecision: {precision*100}")
print(f"recall: {recall*100}")
print(f"fmeasure: {fmeasure*100}")