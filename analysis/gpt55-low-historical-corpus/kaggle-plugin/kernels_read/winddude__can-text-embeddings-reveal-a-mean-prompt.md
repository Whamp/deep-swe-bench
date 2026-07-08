Reading kernel: winddude/can-text-embeddings-reveal-a-mean-prompt
Cells: 13 (6 code, 7 markdown) | 3408 chars

                   Can Text Embeddings reveal a mean prompt?                    

This notebook uses vec2text in an attempt to recover a mean prompt for a list of
prompts.                                                                        

Reference paper: Text Embeddings Reveal (Almost) As Much As Text                

Theries                                                                         

 1 A text string that lies close to the center of an high-demensionality        
   embedding space, constructed from prompts, might score well in a hunt for a  
   "dumb mean prompt".                                                          
 2 A dataset that generates a mean prompt that scores well might mean that      
   dataset will score higher in LB. This could be a quick way to evaluate       
   datasets before fine tuning.                                                 

--------------------------------------------------------------------------------

Imports & installs                                                              

--------------------------------------------------------------------------------

                                                                                
 !pip install polars                                                            
 !pip install vec2text                                                          
 !pip install transformers                                                      
                                                                                

--------------------------------------------------------------------------------

                                                                                
 import polars as pl                                                            
 import vec2text                                                                
 import torch                                                                   
 from transformers import AutoModel, AutoTokenizer, PreTrainedTokenizer,        
 PreTrainedModel                                                                
                                                                                

--------------------------------------------------------------------------------

Get the dataset                                                                 

We'll use ChatGPT Rewrite Promts as it seems to have a decent set of diverse    
prompts.                                                                        

--------------------------------------------------------------------------------

                                                                                
 df_csv = pl.read_csv("/kaggle/input/chatgpt-rewrite-promts/prompts.csv")       
 prompts = df_csv['rewrite_prompt'].to_list()                                   
                                                                                

--------------------------------------------------------------------------------

import the models and vec2text corrector                                        

--------------------------------------------------------------------------------

                                                                                
 encoder =                                                                      
 AutoModel.from_pretrained("sentence-transformers/gtr-t5-base").encoder.to("cud 
 a")                                                                            
 tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/gtr-t5-base") 
 corrector = vec2text.load_pretrained_corrector("gtr-base")                     
                                                                                

--------------------------------------------------------------------------------

our function to get the emedings                                                

--------------------------------------------------------------------------------

                                                                                
 def get_gtr_embeddings(                                                        
     text_list,                                                                 
     encoder: PreTrainedModel,                                                  
     tokenizer: PreTrainedTokenizer                                             
 ) -> torch.Tensor:                                                             
                                                                                
     inputs = tokenizer(                                                        
         text_list,                                                             
         return_tensors="pt",                                                   
         max_length=128,                                                        
         truncation=True,                                                       
         padding="max_length"                                                   
     ).to("cuda")                                                               
                                                                                
     with torch.no_grad():                                                      
         model_output = encoder(input_ids=inputs['input_ids'],                  
 attention_mask=inputs['attention_mask'])                                       
         hidden_state = model_output.last_hidden_state                          
         embeddings = vec2text.models.model_utils.mean_pool(hidden_state,       
 inputs['attention_mask'])                                                      
                                                                                
     return embeddings                                                          
                                                                                

--------------------------------------------------------------------------------

get the embeddings and use vec2text to retrieve a sentence from the mean        
embeddings                                                                      

--------------------------------------------------------------------------------

                                                                                
 embeddings = get_gtr_embeddings(prompts, encoder, tokenizer)                   
                                                                                
 vec2text.invert_embeddings(                                                    
     embeddings=embeddings.mean(dim=0, keepdim=True).cuda(),                    
     corrector=corrector,                                                       
     num_steps=20,                                                              
     sequence_beam_width=4,                                                     
 )                                                                              
                                                                                

--------------------------------------------------------------------------------

Ending Notes                                                                    

Expirment 1                                                                     

Dataset:                                                                        

https://www.kaggle.com/datasets/ilanmeissonnier/chatgpt-rewrite-promts/data     

Yielded the mean prompt of:                                                     

"How to translate this into a set of words and present it as a narrative of a   
conversation between characters in a fictional spacefaring universe"            

and scored scored:                                                              

0.49 in LB (notebook:                                                           
https://www.kaggle.com/code/winddude/dumb-mean-hunt-exp?scriptVersionId=16873147
7)                                                                              

Thoughts:                                                                       

 • mean prompt trended to twards specifics                                      
 • try a large dataset, but need to be careful, a number of public data sets    
   always refer to the "orginal text" as "text" not the actual content such as  
   essay, article, paragraph, etc. (We don't really know what the final test set
   looks like. Concerns that prompts in public datasets may already be trending 
   towards statistical avgs, since they are syntehietic from llms.              
 • try a human revied dataset                                                   
