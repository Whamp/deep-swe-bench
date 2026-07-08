Reading kernel: richolson/t5-prompt-scoring-playground
Cells: 16 (8 code, 8 markdown) | 5725 chars

   Let's look at T5 scores for a test prompt against a larger set of prompts!   

This notebook was inspired by "universal" prompts like "Improve the text to     
this" scoring well                                                              

Maybe you can use it to fine-tune your prompt up the LB a bit?                  

(this notebook now supports GPU - speeds things up a bunch!)                    

--------------------------------------------------------------------------------

                                                                                
 !pip -q install sentence-transformers                                          
                                                                                
 from sentence_transformers import SentenceTransformer                          
 import numpy as np # linear algebra                                            
 import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)         
 from transformers import AutoTokenizer, AutoModel                              
 import torch                                                                   
 import matplotlib.pyplot as plt                                                
                                                                                

--------------------------------------------------------------------------------

                          Load up 400 Re-write prompts                          

--------------------------------------------------------------------------------

                                                                                
 #how many prompts we get per source                                            
 samples_per_source = 200                                                       
                                                                                
 #600 GPT4 prompts I made:                                                      
 https://www.kaggle.com/datasets/richolson/600-gpt4-re-write-prompts            
 gpt4_prompts =                                                                 
 pd.read_csv('/kaggle/input/600-gpt4-re-write-prompts/gpt4_prompts.csv').prompt 
 gpt4_prompts = gpt4_prompts.sample(n=samples_per_source, random_state=42)      
                                                                                
 #Some gemma prompts from nbroad:                                               
 https://www.kaggle.com/datasets/nbroad/gemma-rewrite-nbroad                    
 gemma_prompts =                                                                
 pd.read_csv('/kaggle/input/gemma-rewrite-nbroad/nbroad-v2.csv').rewrite_prompt 
 gemma_prompts = gemma_prompts.sample(n=samples_per_source, random_state=42)    
                                                                                
 #toss the together (order doesn't matter)                                      
 compare_prompts = pd.concat([gpt4_prompts, gemma_prompts], ignore_index=True)  
                                                                                
 compare_prompts                                                                
                                                                                

--------------------------------------------------------------------------------

                             Load sentence-t5-base                              

--------------------------------------------------------------------------------

                                                                                
 model = SentenceTransformer('sentence-t5-base')                                
                                                                                
 if torch.cuda.is_available():                                                  
     model = model.to(torch.device("cuda"))                                     
                                                                                

--------------------------------------------------------------------------------

                        Define the scoring functionality                        

--------------------------------------------------------------------------------

                                                                                
 # Function to calculate sharpened cosine similarity                            
 def sharpened_cosine_similarity(vec1, vec2, exponent=3):                       
     cosine_similarity = torch.nn.functional.cosine_similarity(vec1, vec2,      
 dim=0)                                                                         
     return cosine_similarity ** exponent                                       
                                                                                
                                                                                
 #provides similarity scores of a test_phrase against an array of phrases       
 def compare_phrases(test_phrase, phrases):                                     
     scores = []                                                                
     test_embedding = model.encode(test_phrase, convert_to_tensor=True,         
 show_progress_bar=False)                                                       
                                                                                
     for phrase in phrases:                                                     
         compare_embedding = model.encode(phrase, convert_to_tensor=True,       
 show_progress_bar=False)                                                       
         score = sharpened_cosine_similarity(test_embedding,                    
 compare_embedding).item()                                                      
         scores.append(score)                                                   
                                                                                
     return scores                                                              
                                                                                

--------------------------------------------------------------------------------

                   Chart a few prompts we have scores for...                    

https://www.kaggle.com/code/dipamc77/lb-0-6-improve-the-text-to-this            

https://www.kaggle.com/code/richolson/test-prompt-make-this-text-more-positive  

https://www.kaggle.com/code/richolson/test-prompt-make-this-text-more-negative  

--------------------------------------------------------------------------------

                                                                                
 improve_text_scores = compare_phrases("Improve the text to this.",             
 compare_prompts)   #scored .60 on LB                                           
 positive_text_scores = compare_phrases("Make this text more positive.",        
 compare_prompts)   #scored .56 on LB                                           
 negative_text_scores = compare_phrases("Make this text more negative.",        
 compare_prompts)   #scored .45 on LB                                           
                                                                                
 plt.hist(improve_text_scores, bins=10, alpha=0.5, label='Improve Text',        
 color='yellow')                                                                
 plt.hist(positive_text_scores, bins=10, alpha=0.5, label='Positive Text',      
 color='red')                                                                   
 plt.hist(negative_text_scores, bins=10, alpha=0.5, label='Negative Text',      
 color='blue')                                                                  
                                                                                
 # Add labels and title                                                         
 plt.xlabel('Scores')                                                           
 plt.ylabel('Frequency')                                                        
 plt.title('Distribution of Prompt Scores')                                     
                                                                                
 plt.legend(loc='upper right')                                                  
                                                                                
 plt.show()                                                                     
                                                                                

--------------------------------------------------------------------------------

                          Some more prompt candidates                           

--------------------------------------------------------------------------------

                                                                                
 #don't forget commas!                                                          
                                                                                
 prompt_candidates = [                                                          
     "Refine the following passage by emulating the writing style of [insert    
 desired style here], with a focus on enhancing its clarity, elegance, and      
 overall impact. Preserve the essence and original meaning of the text, while   
 meticulously adjusting its tone, vocabulary, and stylistic elements to         
 resonate with the chosen style.Please improve the following text using the     
 writing style of, maintaining the original meaning but altering the tone,      
 diction, and stylistic elements to match the new style.Enhance the clarity,    
 elegance, and impact of the following text by adopting the writing style of ,  
 ensuring the core message remains intact while transforming the tone, word     
 choice, and stylistic features to align with the specified style.",            
     "Please revise this text to make it more readable and engaging.",          
     "Make this text more fun.",                                                
     "Convert this into a sea shanty.",                                         
     "The composition stands as a sequence of words arranged for potential      
 contemplation, devoid of explicit intent or discernible purpose. It exists     
 within a framework of neutrality, offering neither direction nor conclusion,   
 inviting observation without expectation. The arrangement facilitates a space  
 for presence, unattached to specific outcomes or interpretations.",            
     "Wow - it's hot out today!",                                               
     "Argylle is a dazzlingly eccentric and thrilling film, a wild ride through 
 a landscape of unbridled creativity that, for reasons shrouded in mystery,     
 faced unwarranted critique. At the heart of its intrigue might be its          
 unexpected female protagonist, a twist that sets it apart and perhaps stirred  
 the pot of traditional expectations.",                                         
 ]                                                                              
                                                                                

--------------------------------------------------------------------------------

                           Display the score average                            

--------------------------------------------------------------------------------

                                                                                
 for prompt in prompt_candidates:                                               
     scores = compare_phrases(prompt, compare_prompts)                          
                                                                                
     if len(prompt) > 60: prompt = prompt[:57] + "..."                          
     print(f"{prompt.ljust(60)}    Average Score: {format(np.mean(scores),      
 '.2f')}")                                                                      
                                                                                

--------------------------------------------------------------------------------

                             Just a simple example                              

--------------------------------------------------------------------------------

                                                                                
 def show_prompt_score(test_prompt):                                            
     test_scores = compare_phrases(test_prompt, compare_prompts)                
     print (f"Average Score: {format(np.mean(test_scores), '.2f')}")            
                                                                                
 show_prompt_score("Make this text fun to read.")                               
                                                                                
