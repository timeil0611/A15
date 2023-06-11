import pymysql

conn=pymysql.connect(host='127.0.0.1',
                port=3306,
                user='root',
                passwd='1111',
                database='stock')

coursor=conn.cursor()

create_table_query="""
CREATE TABLE `stock`.`shares` (
  `share_record_no` INT NOT NULL AUTO_INCREMENT,
  `share_id` VARCHAR(45) NOT NULL,
  `trading_volume` INT NOT NULL,
  `open` DOUBLE NOT NULL,
  `close` DOUBLE NOT NULL,
  `min` DOUBLE NOT NULL,
  `max` DOUBLE NOT NULL,
  `date`DATE NOT NULL,
  PRIMARY KEY (`share_record_no`));
  """
coursor.execute(create_table_query)
conn.commit()
conn.close()