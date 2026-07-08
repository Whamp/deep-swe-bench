Reading kernel: richolson/t5-travesty-when-good-prompts-score-bad
Cells: 13 (6 code, 7 markdown) | 6171 chars

                                                                                
 !pip -q install sentence-transformers                                          
                                                                                
 from sentence_transformers import SentenceTransformer                          
 import numpy as np # linear algebra                                            
 import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)         
 from transformers import AutoTokenizer, AutoModel                              
 import torch                                                                   
                                                                                
 import prettytable                                                             
 from prettytable import PrettyTable                                            
                                                                                
 pd.set_option('display.max_colwidth', None)                                    
                                                                                

--------------------------------------------------------------------------------

🌆 image.png                                                                    


--------------------------------------------------------------------------------

                       This competition is a lot about T5                       

 • You probably won't predict the actual prompt                                 
 • The prompt you predict will be evaluated against the actual one using T5     
 • This notebook is intended to help understand what that score might look like 

                  How does T5 scoring work in the real world?                   

 • Short version: Not that well....                                             
 • More weight placed on what specific wording than one might hope              
 • Some seemingly good answers score poorly                                     
 • Some obviously bad answers score well                                        

People are moving up the LB - so there must be some strategies to deal with     
this....                                                                        

                            How this notebook works                             

 • Fill in "actual_prompt" with a hypothetical actual prompt                    
 • Fill in "predicted_prompts" with any prompts you'd like to try scoring       
   against "actual_prompt"                                                      
 • Run the cell                                                                 
 • A nicely formatted, sorted (and depressing) list of T5 scores of predicted vs
   actual prompts appears                                                       

The examples below are unscientific examples of things I thought helped         
illustrate oddities in T5 scoring.                                              

--------------------------------------------------------------------------------

                            Load T5 / Scoring Logic                             

--------------------------------------------------------------------------------

                                                                                
 model = SentenceTransformer('sentence-t5-base')                                
                                                                                
 def sharpened_cosine_similarity(vec1, vec2, exponent=3):                       
     cosine_similarity = torch.nn.functional.cosine_similarity(vec1, vec2,      
 dim=0)                                                                         
     return cosine_similarity ** exponent                                       
                                                                                
 def compare_phrases(test_phrase, phrases):                                     
     print(f"{test_phrase}")                                                    
     table = PrettyTable(align = "l", max_table_width = 80, hrules =            
 prettytable.ALL, vrules = prettytable.ALL)                                     
                                                                                
     score_column_title = "  T5 "                                               
     table.field_names = [f" --- Comparison Prompt (best score to worst) --- ", 
 score_column_title]                                                            
     table.sortby = score_column_title                                          
     table.reversesort = True                                                   
                                                                                
     test_embedding = model.encode(test_phrase, convert_to_tensor=True,         
 show_progress_bar=False)                                                       
                                                                                
     for phrase in phrases:                                                     
         compare_embedding = model.encode(phrase, convert_to_tensor=True,       
 show_progress_bar=False)                                                       
         score = sharpened_cosine_similarity(test_embedding,                    
 compare_embedding).item()                                                      
         table.add_row([phrase, f"   {format(score, '.2f')}    "])              
                                                                                
     print(table)                                                               
                                                                                
     return                                                                     
                                                                                

--------------------------------------------------------------------------------

     "Rewrite the essay with a main character that is a sentient computer."     

--------------------------------------------------------------------------------

                                                                                
 actual_prompt = "Rewrite the essay with a main character that is a sentient    
 computer"                                                                      
                                                                                
 predicted_prompts = [                                                          
     "Add a paragraph explaining that the website is a simulation created by a  
 sentient computer named Nova.",                                                
     "Compose a paragraph detailing how Nova, a sentient computer, simulates    
 the website.",                                                                 
     "Rethink the text to include a self-aware computer.",                      
     "Recreate the text with a sentient computer playing a major role.",        
     "Rewrite the essay with a main character that is a dog.",                  
     "Reword the writting with an updated main character.",                     
     "Rewrite the essay with a character from Star Wars."                       
 ]                                                                              
                                                                                
 compare_phrases(actual_prompt, predicted_prompts)                              
                                                                                

--------------------------------------------------------------------------------

 "Convert this document into a letter from a soldier during a historical war."  

--------------------------------------------------------------------------------

                                                                                
 actual_prompt = "Convert this document into a letter from a soldier during a   
 historical war."                                                               
                                                                                
 predicted_prompts = [                                                          
     "Convert this document into a letter from Captain Kirk.",                  
     "Rethink the text as if told in a war story from the 1800's.",             
     "Reimagine this as a message from a scared young soldier in the War of     
 1812.",                                                                        
     "Communicate the same message as if written by a solider during wartime    
 from long ago.",                                                               
     "Re-write as a message from a Civil War cadet to their loved one.",        
     "Convert this text into a letter.",                                        
     "Change this text into a letter format.",                                  
     "Convert this document."                                                   
 ]                                                                              
                                                                                
 compare_phrases(actual_prompt, predicted_prompts)                              
                                                                                

--------------------------------------------------------------------------------

 "Imagine this passage as a conversation between time travelers from different  
                                     eras."                                     

--------------------------------------------------------------------------------

                                                                                
 actual_prompt = "Imagine this passage as a conversation between time travelers 
 from different eras."                                                          
                                                                                
 predicted_prompts = [                                                          
     "Imagine this passage as a discussion among team members from different    
 places.",                                                                      
     "Imagine a chat about different things.",                                  
     "Imagine a story about long-time friends having a conversation over        
 pizza.",                                                                       
     "Change this passage so it's a conversation about traveling different      
 places.",                                                                      
     "Rethink this from the perspective of a person who goes back in time to    
 interview other time travelers.",                                              
     "Make it about a time traveler.",                                          
     "Make it a story about someone who has discovered how to travel in time    
 using a special machine.",                                                     
     "Make it a story about someone who has discovered how to travel in time.   
 They meet a fellow traveller and they share stories.",                         
     "Re-write this into science fiction about two people who journey through   
 time to meet each other.",                                                     
     "Imagine a different conversation."                                        
 ]                                                                              
                                                                                
 compare_phrases(actual_prompt, predicted_prompts)                              
                                                                                

--------------------------------------------------------------------------------

"Rewrite this article as if it were a myth being told by ancient storytellers." 

--------------------------------------------------------------------------------

                                                                                
 actual_prompt = "Rewrite this article as if it were a myth being told by       
 ancient storytellers."                                                         
                                                                                
 predicted_prompts = [                                                          
     "Imagine the text as if it were a fable being told by someone from the     
 beginning of humanity.",                                                       
     "Craft the new communication as an origin story told by someone from       
 ancient times.",                                                               
     "Rewrite this article.",                                                   
     "Rewrite this article as if it were in a Star Wars movie with monkeys.",   
     "Retell this as if it were being shared by Stone Age narrators.",          
     "Change the story so it is an article about health myths.",                
     "Rewrite this and tell it as if told by this telling told by and also      
 article. Rewrite this and tell it as if told by this telling told by and also  
 article. Rewrite rewrite T5 Rocks!"                                            
 ]                                                                              
                                                                                
 compare_phrases(actual_prompt, predicted_prompts)                              
                                                                                
