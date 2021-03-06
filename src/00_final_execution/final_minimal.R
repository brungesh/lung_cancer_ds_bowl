library(data.table)
library(pROC)
library(dplyr)
library(LiblineaR)

# INITIAL SETUP -----------------------------------------------------------------

MultiLogLoss = function(act, pred){
  eps = 1e-15
  pred = pmin(pmax(pred, eps), 1 - eps)
  sum(act * log(pred) + (1 - act) * log(1 - pred)) * -1/NROW(act)
}

# global paths
source("config.R")

# # file locations
# path_repo <<- "~/lung_cancer_ds_bowl/"
# path_dsb <<- "/home/shared/output/"
# ANNOTATIONS_FILE = paste0(path_repo,"/data/stage1_labels.csv")  # JUST FOR TRAINING
# SUBMISSIONS_FILE = paste0(path_repo,"/data/stage1_sample_submission.csv")
# DL1_FILE = paste0(path_dsb,"resnet/nodules_patches_dl1_v11.csv")
# DL2_FILE = paste0(path_dsb,"resnet/nodules_patches_hardnegative_v03.csv")
# NODULES_EXTENDED_FILE = paste0(path_dsb,"resnet/nodules_patches_dl1_v11_score07_noduleaggr_augmented.csv")
# DL3_FILE = paste0(path_dsb,"resnet/nodules_patches_dl3_v02.csv")
# DL3_VALIDATION_FILE = paste0(path_repo, 'data/stage1_validation.csv')
# FINAL_MODEL_01 = "final_model_01.rda"
# FINAL_MODEL_02 = "final_model_02.rda"
# SUBMISSION_OUTPUT01 = paste0(path_dsb, 'submissions/final_submission_01.csv')
# SUBMISSION_OUTPUT02 = paste0(path_dsb, 'submissions/final_submission_02.csv')


# FEATURES -----------------------------------------------------------------

dl1 = fread(DL1_FILE)
dl2 = fread(DL2_FILE)

dl12 = merge(dl1, dl2, by=c('patientid','nslice','x','y','diameter'))
dl12[,score:=(score.x+score.y)/2]
dl12[,score.x:=NULL]
dl12[,score.y:=NULL]
# write.csv(dl12, '/home/mingot/tmp/input_aggregation.csv', row.names=F, quote=F)
# python mergeNodules.py -t 0.5 ~/tmp/input_aggregation.csv ~/tmp/output_aggregation.csv

dl12 = dl12[score>0.7]
dl12_final = dl12[,.(max_diameter_patches = max(diameter, na.rm=T),
                     max_score_patches = max(score, na.rm=T)),
                  by=patientid]

# FEATURES augment (previous with aggregation and augmentation)
df_nodule = fread(NODULES_EXTENDED_FILE)
df_nodule = plyr::ddply(
  df_nodule, "patientid", 
  function(df) {
    df_max = df[which.max(df$score), ]
    df_max$patientid = NULL
    df_max$nslicespread_sd = sd(df$nslicesSpread) 
    names(df_max) = paste0("maxscorenod_", names(df_max))
    
    df_maxd = df[which.max(df$diameter), ]
    df_maxd$patientid = NULL
    names(df_maxd) = paste0("maxdiamnod_", names(df_maxd))
    
    data.table(df_max, df_maxd, stringsAsFactors = FALSE)
  }, .progress = "text"
) %>% as.data.table
df_nodule = df_nodule[,.(patientid, maxscorenod_nslicespread_sd, maxscorenod_PC1_lbp, maxscorenod_10_lungmask, 
                         maxscorenod_y, maxscorenod_PC3_lbp,maxdiamnod_PC2_hog, maxdiamnod_x, 
                         maxdiamnod_40_nodeverticalposition)]


# DL3 features (just used for model 02)
dl3_df = fread(DL3_FILE)
dl3_df = dl3_df[,.(dl3_max=max(score), 
                   dl3_has=as.numeric(sum(score>0.7)>0),
                   dl3_nohas=as.numeric(sum(score<.3)==.N)),by=patientid]


# model 01 TRAIN -------------------------------------------------------------------

# # create data train df
# data_train = fread(ANNOTATIONS_FILE)
# setnames(data_train,'id','patientid')
# data_train[,patientid:=paste0("dsb_",patientid,".npz")]
# data_train = merge(data_train, dl12_final, by='patientid', all.x=T)
# data_train = merge(data_train, df_nodule, by='patientid', all.x=T)  # TODO: check if we are getting all the filenames
# data_train[is.na(data_train)] = 0
# 
# vars_sel = c('max_diameter_patches','max_score_patches','maxscorenod_PC1_lbp', 'maxscorenod_nslicespread_sd',
#              "maxscorenod_10_lungmask",'maxscorenod_y', "maxscorenod_PC3_lbp","maxdiamnod_40_nodeverticalposition", "maxdiamnod_x","maxdiamnod_PC2_hog")
# 
# aucs = c(); lls = c()
# for(i in 1:50){
#   k = 3; data_train$id = sample(1:k, nrow(data_train), replace = TRUE); list = 1:k
#   for (i in 1:k){
#     trainingset = subset(data_train, id %in% list[-i])
#     testset = subset(data_train, id %in% c(i))
#     
#     # train
#     mymodel = glm(cancer ~ 1 + ., family=binomial(link='logit'), data=trainingset[,c("cancer",vars_sel),with=F])
#     
#     # test
#     pred = predict(mymodel, testset[,c("cancer",vars_sel),with=F], type="response")
#     real = testset$cancer
#     
#     # store results
#     aucs = c(aucs, auc(real,pred))
#     lls = c(lls, MultiLogLoss(real,pred))
#   }
# }
# summary(mymodel); summary(aucs); summary(lls)
# 
# # store final model
# final_model_01 = glm(cancer ~ 1 + ., family=binomial(link='logit'), data=data_train[,c("cancer",vars_sel),with=F])
# summary(final_model_01)
# save(final_model_01, file=FINAL_MODEL_01)

# model 01 EXECUTION ------------------------------------------------------

# construct table test
data_test = fread(SUBMISSIONS_FILE)
setnames(data_test,'id','patientid')
data_test[,patientid:=paste0("dsb_",patientid,".npz")]
data_test = merge(data_test, dl12_final, by='patientid', all.x=T)
data_test = merge(data_test, df_nodule, by='patientid', all.x=T)  
data_test[is.na(data_test)] = 0


load(FINAL_MODEL_01)
vars_sel01 = c('max_diameter_patches','max_score_patches','maxscorenod_PC1_lbp', 'maxscorenod_nslicespread_sd',
               "maxscorenod_10_lungmask",'maxscorenod_y', "maxscorenod_PC3_lbp","maxdiamnod_40_nodeverticalposition", "maxdiamnod_x","maxdiamnod_PC2_hog")
preds01 = predict(final_model_01, data_test[,vars_sel01,with=F], type="response")
submission01 = data.table(id=gsub(".npz|dsb_","",data_test$patientid), cancer=preds01)
cat("Mean cancer in submission01:", mean(submission01$cancer),"\n")
write.csv(submission01, SUBMISSION_OUTPUT01, quote=F, row.names=F)
write.csv(submission01, "/home/shared/output/submissions/final_submission_01_v02.csv", quote=F, row.names=F)


# model 02 TRAIN ----------------------------------------------------------------

# # validation patients
# validation = fread(DL3_VALIDATION_FILE)
# 
# # create data train df
# data_train = fread(ANNOTATIONS_FILE)
# setnames(data_train,'id','patientid')
# data_train[,patientid:=paste0("dsb_",patientid,".npz")]
# data_train = merge(data_train, dl12_final, by='patientid', all.x=T)
# data_train = merge(data_train, df_nodule, by='patientid', all.x=T)  # TODO: check if we are getting all the filenames
# data_train = merge(data_train, dl3_df, by='patientid', all.x=T)
# data_train[is.na(dl3_nohas), dl3_nohas:=1]
# data_train[is.na(data_train)] = 0  # replace NA's with 0's
# 
# data_train = data_train[patientid%in%validation$patientid]
# #vars_sel = c('max_diameter_patches','maxscorenod_nslicespread_sd','dl3_has','maxscorenod_PC1_lbp')  # old
# vars_sel = c('max_diameter_patches','maxscorenod_nslicespread_sd','dl3_has','maxdiamnod_40_nodeverticalposition')  # new
# 
# aucs = c(); lls = c()
# for(i in 1:100){
#   k = 3; data_train$id = sample(1:k, nrow(data_train), replace = TRUE); list = 1:k
#   for (i in 1:k){
#     trainingset = subset(data_train, id %in% list[-i])
#     testset = subset(data_train, id %in% c(i))
#     
#     # train
#     mymodel = glm(cancer ~ 1 + ., family=binomial(link='logit'), data=trainingset[,c("cancer",vars_sel),with=F])
#     
#     # test
#     pred = predict(mymodel, testset[,c("cancer",vars_sel),with=F], type="response")
#     real = testset$cancer
#     
#     # store results
#     aucs = c(aucs, auc(real,pred))
#     lls = c(lls, MultiLogLoss(real,pred))
#   }
# }
# summary(mymodel); summary(aucs); summary(lls)
# 
# # store final model
# final_model_02 = glm(cancer ~ 1 + ., family=binomial(link='logit'), data=data_train[,c("cancer",vars_sel),with=F])
# summary(final_model_02)
# save(final_model_02, file=FINAL_MODEL_02)


# model 02 EXECUTION ------------------------------------------------------

data_test = fread(SUBMISSIONS_FILE)
setnames(data_test,'id','patientid')
data_test[,patientid:=paste0("dsb_",patientid,".npz")]
data_test = merge(data_test, dl12_final, by='patientid', all.x=T)
data_test = merge(data_test, df_nodule, by='patientid', all.x=T)
data_test = merge(data_test, dl3_df, by='patientid', all.x=T)
data_test[is.na(dl3_nohas), dl3_nohas:=1]
data_test[is.na(data_test)] = 0

load(FINAL_MODEL_02)
vars_sel02 = vars_sel = c('max_diameter_patches','maxscorenod_nslicespread_sd','maxdiamnod_40_nodeverticalposition','dl3_has')
preds02 = predict(final_model_02, data_test[,vars_sel02,with=F], type="response")
submission02 = data.table(id=gsub(".npz|dsb_","",data_test$patientid), cancer=preds02)
cat("Mean cancer in submission02:", mean(submission02$cancer),"\n")
# submission02[,cancer:=cancer-mean(cancer)+0.2591267]  # fix bias in the 400 patients data
# summary(submission03$cancer)
write.csv(submission02, SUBMISSION_OUTPUT02, quote=F, row.names=F)


