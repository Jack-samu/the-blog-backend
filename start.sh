#! /bin/sh

MAX_RETRIES=3
RETRY_CNT=0

if [ ! -d "migrations" ]; then

    echo "待Mysql可用"
    until mariadb --host=$MYSQL_HOST --user=$MYSQL_USER --password=$MYSQL_PWD -D $MYSQL_DATABASE -e "select 1" --skip-ssl; do
        RETRY_CNT=$((RETRY_CNT + 1))
        if [ $RETRY_CNT -ge $MAX_RETRIES ]; then
            echo "超过最大重试次数，退出"
            exit 1
        fi
        echo "mysql连通性测试失败"
        sleep 2
    done

    echo "数据库迁移前置动作进行"
    flask db init
    flask db migrate -m "initial migration"
    flask db upgrade   
    
    echo "导入初始化数据"
    mariadb --host=$MYSQL_HOST --user=$MYSQL_USER --password=$MYSQL_PWD -D $MYSQL_DATABASE --skip-ssl < ./db/data/blog_data.sql

else
    echo "migrations已存在，不用初始化了"
fi

# gunicorn启动项目
gunicorn -c conf.py "app:create_app()" --capture-output