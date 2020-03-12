#-*- coding: utf-8 -*-
'''
Created on 2015-06-22

@author: Lockvictor
'''
import os
os.chdir("C:\\Users\\ShangFR\\Desktop\\ml-1m\\MovieLens-RecSys-master")   #修改当前工作目录
os.getcwd()

from log.log_test import Logger

Logger('log\\error.log', level='error').logger.error('error')
log = Logger('log\\all.log',level='debug')
log.logger.debug('debug')
log.logger.info('info')
log.logger.warning('警告')
log.logger.error('报错')
log.logger.critical('严重')
    
    
import sys
import random
import math
import os
from operator import itemgetter

from collections import defaultdict

random.seed(0)

# In[0]:
class UserBasedCF(object):
    ''' TopN recommendation - User Based Collaborative Filtering '''

    def __init__(self):
        self.trainset = {}
        self.testset = {}

        self.n_sim_user = 20
        self.n_rec_movie = 10

        self.user_sim_mat = {}
        self.movie_popular = {}
        self.movie_count = 0

        log.logger.info('Similar user number = %d' % self.n_sim_user)
        log.logger.info('recommended movie number = %d' % self.n_rec_movie)

    @staticmethod
    def loadfile(filename):
        ''' load a file, return a generator. '''
        try:
            fp = open(filename, 'r')
        except Exception as e:
            log.logger.exception("Unable to open data. Error: %s", e)
        for i, line in enumerate(fp):
            yield line.strip('\r\n')
            if i % 100000 == 0:
                log.logger.info('loading %s(%s)' % (filename, i))
        fp.close()
        log.logger.info('load %s succ' % filename)

    def generate_dataset(self, filename, pivot=0.7):
        ''' load rating data and split it to training set and test set '''
        trainset_len = 0
        testset_len = 0

        for line in self.loadfile(filename):
            #user, movie, rating, _ = line.split('::')
            _,movie, user, _, rating, _ , _ = line.split(',')
            # 评价转换
            if isinstance(rating,int):
                rating = 2 if int(rating)>10 else 1
            else:
                rating = 0
            
            # split the data by pivot
            if random.random() < pivot:
                self.trainset.setdefault(user, {})
                self.trainset[user][movie] = int(rating)
                trainset_len += 1
            else:
                self.testset.setdefault(user, {})
                self.testset[user][movie] = int(rating)
                testset_len += 1

        log.logger.info('split training set and test set succ')
        log.logger.info('train set = %s' % trainset_len)
        log.logger.info('test set = %s' % testset_len)
        
    def add_dataset(self, filename):
        ''' load rating data and add to training set'''
        trainset_len = len(self.trainset)
        trainset_len0 = trainset_len
        for line in self.loadfile(filename):
            #user, movie, rating, _ = line.split('::')
            _,movie, user, _, rating, _ , _ = line.split(',')
            if isinstance(rating,int):
                rating = 2 if int(rating)>10 else 1
            else:
                rating = 0
            
            self.trainset.setdefault(user, {})
            self.trainset[user][movie] = int(rating)
            trainset_len += 1

        print ('add data set = %s' % (trainset_len-trainset_len0), file=sys.stderr)

    def calc_user_sim(self):
        ''' calculate user similarity matrix '''
        # build inverse table for item-users
        # key=movieID, value=list of userIDs who have seen this movie
        print ('building movie-users inverse table...', file=sys.stderr)
        movie2users = dict()

        for user, movies in self.trainset.items():
            for movie in movies:
                # inverse table for item-users
                if movie not in movie2users:
                    movie2users[movie] = set()
                movie2users[movie].add(user)
                # count item popularity at the same time
                if movie not in self.movie_popular:
                    self.movie_popular[movie] = 0
                self.movie_popular[movie] += 1
        print ('build movie-users inverse table succ', file=sys.stderr)

        # save the total movie number, which will be used in evaluation
        self.movie_count = len(movie2users)
        print ('total movie number = %d' % self.movie_count, file=sys.stderr)

        # count co-rated items between users
        usersim_mat = self.user_sim_mat
        print ('building user co-rated movies matrix...', file=sys.stderr)

        for movie, users in movie2users.items():
            for u in users:
                usersim_mat.setdefault(u, defaultdict(int))
                for v in users:
                    if u == v:
                        continue
                    usersim_mat[u][v] += 1
        print ('build user co-rated movies matrix succ', file=sys.stderr)

        # calculate similarity matrix
        print ('calculating user similarity matrix...', file=sys.stderr)
        simfactor_count = 0
        PRINT_STEP = 2000000

        for u, related_users in usersim_mat.items():
            for v, count in related_users.items():
                usersim_mat[u][v] = count / math.sqrt(
                    len(self.trainset[u]) * len(self.trainset[v]))
                simfactor_count += 1
                if simfactor_count % PRINT_STEP == 0:
                    print ('calculating user similarity factor(%d)' %
                           simfactor_count, file=sys.stderr)

        print ('calculate user similarity matrix(similarity factor) succ',
               file=sys.stderr)
        print ('Total similarity factor number = %d' %
               simfactor_count, file=sys.stderr)

    def recommend(self, user):
        ''' Find K similar users and recommend N movies. '''
        K = self.n_sim_user
        N = self.n_rec_movie
        rank = dict()
        
        # 判断有无购买记录
        if self.trainset.get(user): # right:这种通过key来查询是否存在的方式是比较好的
            watched_movies = self.trainset[user]
            # 基于用户相似矩阵的N个产品推荐
            while len(rank)<N:
                for similar_user, similarity_factor in sorted(self.user_sim_mat[user].items(),
                                                              key=itemgetter(1), reverse=True)[0:K]:
                    for movie in self.trainset[similar_user]:
                        if movie in watched_movies:
                            continue
                        # predict the user's "interest" for each movie
                        rank.setdefault(movie, 0)
                        rank[movie] += similarity_factor
                K = K*2
                if K > 100:
                    print ('比对了%d个用户，找了 %d个产品' %(K,len(rank)))
                    if len(rank) == 0:
                        rank = sorted(self.movie_popular.items(), key=itemgetter(1), reverse=True)[0:N]
                        rank = dict(rank)
                        print ('高频推荐')
                    break
        else:
            rank = sorted(self.movie_popular.items(), key=itemgetter(1), reverse=True)[0:N]
            rank = dict(rank)
            print ('新用户，高频推荐')
        # return the N best movies
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[0:N]

    def evaluate(self):
        ''' print evaluation result: precision, recall, coverage and popularity '''
        print ('Evaluation start...', file=sys.stderr)

        N = self.n_rec_movie
        #  varables for precision and recall
        hit = 0
        rec_count = 0
        test_count = 0
        # varables for coverage
        all_rec_movies = set()
        # varables for popularity
        popular_sum = 0

        for i, user in enumerate(self.trainset):
            if i % 500 == 0:
                print ('recommended for %d users' % i, file=sys.stderr)
            test_movies = self.testset.get(user, {})
            rec_movies = self.recommend(user)
            for movie, _ in rec_movies:
                if movie in test_movies:
                    hit += 1
                all_rec_movies.add(movie)
                popular_sum += math.log(1 + self.movie_popular[movie])
            rec_count += N
            test_count += len(test_movies)

        precision = hit / (1.0 * rec_count)
        recall = hit / (1.0 * test_count)
        coverage = len(all_rec_movies) / (1.0 * self.movie_count)
        popularity = popular_sum / (1.0 * rec_count)

        print ('precision=%.4f\trecall=%.4f\tcoverage=%.4f\tpopularity=%.4f' %
               (precision, recall, coverage, popularity), file=sys.stderr)

# In[1]:
if __name__ == '__main__':
    #ratingfile = os.path.join('ml-1m', 'ratings.dat')
    ratingfile = 'D:\\lczq\\data_stock\\orders2.csv'
    usercf = UserBasedCF()
    usercf.generate_dataset('D:\\lczq\\data_stock\\orders2.csv')
    usercf.add_dataset('D:\\lczq\\data_stock\\orders3.csv')
    usercf.calc_user_sim()
    usercf.evaluate()



usim = usercf.user_sim_mat
uset = usercf.trainset
watched_m = uset['1003']
mp = usercf.movie_popular
usercf.movie_count
usercf.recommend('1003')
usercf.recommend('1237')
usercf.recommend('1018')
usercf.recommend('9686')
# 用户-产品 订单 字典
# 产品销量
# 产品数量
# 用户相似矩阵 

usercf.user_sim_mat=usim
usercf.trainset = uset
usercf.recommend('10032')
uset['1018']
if uset.get('1018'): # right:这种通过key来查询是否存在的方式是比较好的
    print(133)
else:
    print(123)
        uset['1018']
        
# 用户-产品 订单 字典
# 产品销量
# 产品数量
# 用户相似矩阵 

usim['1237'].items()
