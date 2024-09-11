import json
import re
import os

#______________________________________________________________________________
class Dataset:
    # print("Dataset RUNING!")
    def __init__(self, filename):
        self.dictionaryofdocs = {}
        with open(filename, "r") as fh:
            self.pubtaturtext = fh.read()
    def load(self):
        # -----------------------------------------
        # parse data and make list of records
        pattern = "\n\n"
        self.listofdocs = re.split(pattern, self.pubtaturtext)
        # -----------------------------------------
        for doc in self.listofdocs:
            if doc.strip() == '':
                self.listofdocs.remove(doc)
        # -----------------------------------------
        for doc in self.listofdocs:
            doc = doc.strip()
            # [id, record]
            id_record = doc.split('|t|')
            # id [id, -]
            doc_id = id_record[0].strip()
            # create key:val = doc_id:{}
            self.dictionaryofdocs[doc_id] = {}
            # record[-, record]
            record =  id_record[1]
            # record = [titel, rels]
            title_rel = record.split(doc_id)
            # title [title, -]
            title = title_rel[0].strip()
            # create key:val = doc_id:{title:{title}}
            self.dictionaryofdocs[doc_id]["title"] = title
            # append each rel of a record to rels list
            self.dictionaryofdocs[doc_id]["rels"] = []
            for rel in title_rel[1:]:
                rel = rel.strip().split('\t')
                relation = rel[0]
                chemical = rel[1]
                disease = rel[2]
                self.dictionaryofdocs[doc_id]["rels"].append({
                    "relation":relation,
                    "chemical": chemical,
                    "disease":disease
                })
        # -----------------------------------------
        return self.dictionaryofdocs

#______________________________________________________________________________
class Makeprompt:
    # print("Makeprompt RUNING!")
    def __init__(self, dictofdocuments):
        self.dictofdocuments = dictofdocuments

    def prompt(self, doc_id):
        self.doc_id = doc_id
        self.title_as_prompt = self.dictofdocuments[self.doc_id]["title"]
        return self.title_as_prompt
#______________________________________________________________________________
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
from langchain_community.chat_models import ChatOllama

class Llm:
    # print("Llm RUNING!")
    def __init__(self):
                                                                            # Provide my examples
        examples = [
            {
                "input":"Electrocardiographic evidence of myocardial injury in psychiatrically hospitalizedcocaine abusers.The electrocardiograms (ECG) of 99 cocaine-abusing patients were compared with theECGs of 50 schizophrenic controls. Eleven of the cocaine abusers and none of thecontrols had ECG evidence of significant myocardial injury defined as myocardialinfarction, ischemia, and bundle branch block.",
                "output":"""CID***cocaine***myocardial infarction\nCID***cocaine***bundle branch block""",
            },
            {
                "input": "Lidocaine-induced cardiac asystole.Intravenous administration of a single 50-mg bolus of lidocaine in a 67-year-oldman resulted in profound depression of the activity of the sinoatrial andatrioventricular nodal pacemakers. The patient had no apparent associated conditionswhich might have predisposed him to the development of bradyarrhythmias; and, thus,this probably represented a true idiosyncrasy to lidocaine.",
                "output": """CID***Lidocaine***cardiac asystole""",
            },]
                                                                            # Format my examples
        example_prompt = ChatPromptTemplate.from_messages(
            [("human", "{input}"),
                ("ai", "{output}"),])
        
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=examples,
            )
                                                                            # Role messages
        self.final_prompt = ChatPromptTemplate.from_messages(
            [("system", "You are a knowledgeable physician. extract every possible explicit and implicit relations in form of [CID]***[chemical]***[disease]. use original form of chemical or disease in text. do not print any thing other than relations!"),
             few_shot_prompt,
            ("human", "{input}"),])

    def load_params(self, model, temperature=0.0):
        self.model = model
        self.temperature = temperature

    def generate(self, promptt):
        chain = self.final_prompt | ChatOllama(model=self.model, temperature=self.temperature)
        self.output = chain.invoke({"input": promptt}).content
        return self.output

#______________________________________________________________________________

class Pubtatur:
    # print("Pubtatur RUNING!")
    def __init__(self, results_as_dictionary):
        self.results_as_dictionary = results_as_dictionary
    def write(self):
        for doc_id in self.results_as_dictionary.keys():
            # grabs title related to the id from results_as_dictionary
            title_as_promptt = self.results_as_dictionary[doc_id]["prompt"]

            # grabs list of generated rels related to the id from results_as_dictionary
            gen_rels = self.results_as_dictionary[doc_id]["rels"]
            
            save_path = "results.pubtatur.txt"

            with open(save_path, 'a') as file:
                file.write(f"{doc_id}|t|{title_as_promptt}")
                for rel in gen_rels:
                    rel_type = rel["relation"]
                    chemi = rel["chemical"]
                    disea = rel["disease"]
                    file.write(f"\n{doc_id}\t{rel_type}\t{chemi}\t{disea}")
                file.write("\n\n")


        print(f"---------------file as Pubtatur format saved in current directory---------------")

    
#______________________________________________________________________________

class main:
    # print("main RUNING!")
    def __init__(self, filename, modelname, temperature):
        fromdrive = Dataset(filename)
        docs_as_dict = fromdrive.load()
        chat = Llm()
        chat.load_params(model=modelname, temperature=temperature)

        # init Makeprompt object
        make = Makeprompt(docs_as_dict)
        # creating dictionary to put results in it
        results_as_dict = {}
        # creating prompts one by one and pass it to LLM
        passed_docs = 0
        # for docid in list(docs_as_dict.keys())[342:350]:
        for docid in docs_as_dict.keys():
            # set prompt related to id
            my_prompt = make.prompt(docid)
            # pass prompt to llm and get output as list of relations
            llm_output = chat.generate(my_prompt).split("\n")
            print(f"docid: {docid}")
            print(llm_output)
            # break
            # make a dictionary of results
            results_as_dict[docid] = {}
            results_as_dict[docid]["prompt"] = my_prompt
            results_as_dict[docid]["rels"] = []
            for relation in llm_output:
                splitted_relation = relation.split("***")
                rel = splitted_relation[0]
                chem = splitted_relation[1].lower()
                dis = splitted_relation[2].lower()
                results_as_dict[docid]["rels"].append({
                    "relation":rel,
                    "chemical":chem,
                    "disease":dis
                })
            print(f"{passed_docs}/{len(docs_as_dict.keys())}\n")
            
            passed_docs += 1
        make_pub = Pubtatur(results_as_dict)
        make_pub.write()


#______________________________________________________________________________
filename = "test.PubTator_edited.txt"
model = "llama3"
#______________________________________________________________________________
main(filename=filename, modelname=model, temperature=0.2)
