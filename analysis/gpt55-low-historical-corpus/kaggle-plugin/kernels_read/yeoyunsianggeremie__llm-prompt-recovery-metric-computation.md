Reading kernel: yeoyunsianggeremie/llm-prompt-recovery-metric-computation
Cells: 5 (4 code, 1 markdown) | 2365 chars

                    LLM Prompt Recovery | Metric Computation                    

Evaluation Metric Description                                                   

                                                                                
 For each row in the submission and corresponding ground truth,                 
 sentence-t5-base is used to calculate corresponding embedding vectors. The     
 score for each predicted / expected pair is calculated using the Sharpened     
 Cosine Similarity, using an exponent of 3. The SCS is used to attenuate the    
 generous score given by embedding vectors for incorrect answers. Do not leave  
 any rewrite_prompt blank as null answers will throw an error.                  
                                                                                

--------------------------------------------------------------------------------

In this notebook, I show my own implementation of the evaluation metric and     
provide a sample CV calculation on nbroad's generated data                      

Steps                                                                           

 1 Compute the embeddings of the predicted prompts and the actual prompts using 
   sentence-t5-base from HuggingFace                                            
 2 For each row, compute C ** 3, where C is the cosine similarity between the   
   predicted prompt and the actual prompt for each row                          
 3 Finally, average the predictions across the rows to get the CV score         

--------------------------------------------------------------------------------

                                                                                
 !pip install -Uq                                                               
 /kaggle/input/sentence-transformers-2-4-0/sentence_transformers-2.4.0-py3-none 
 -any.whl                                                                       
                                                                                

--------------------------------------------------------------------------------

                                                                                
 import numpy as np                                                             
 import pandas as pd                                                            
 from tqdm import tqdm                                                          
 tqdm.pandas()                                                                  
                                                                                
 import warnings                                                                
 warnings.filterwarnings('ignore')                                              
                                                                                
 from sentence_transformers import SentenceTransformer                          
 from sklearn.metrics.pairwise import cosine_similarity                         
                                                                                

--------------------------------------------------------------------------------

                                                                                
 test = pd.read_csv("/kaggle/input/gemma-rewrite-nbroad/nbroad-v1.csv")         
                                                                                
 #reference:                                                                    
 https://www.kaggle.com/code/isakatsuyoshi/improve-the-following-text-below     
 test["pred"] = 'Improve the following text below:\n\n' +                       
 test['rewritten_text'] #dummy prompt                                           
                                                                                
 test                                                                           
                                                                                

--------------------------------------------------------------------------------

                                                                                
 def CVScore(test):                                                             
                                                                                
     scs = lambda row: abs((cosine_similarity(row["actual_embeddings"],         
 row["pred_embeddings"])) ** 3)                                                 
                                                                                
     model =                                                                    
 SentenceTransformer('/kaggle/input/sentence-t5-base-hf/sentence-t5-base')      
                                                                                
     test["actual_embeddings"] = test["rewrite_prompt"].progress_apply(lambda   
 x: model.encode(x, normalize_embeddings=True,                                  
 show_progress_bar=False).reshape(1, -1))                                       
     test["pred_embeddings"] = test["pred"].progress_apply(lambda x:            
 model.encode(x, normalize_embeddings=True, show_progress_bar=False).reshape(1, 
 -1))                                                                           
                                                                                
     test["score"] = test.apply(scs, axis=1)                                    
                                                                                
     return np.mean(test['score'])[0][0]                                        
                                                                                
 print(f"CV Score: {CVScore(test)}")                                            
                                                                                
