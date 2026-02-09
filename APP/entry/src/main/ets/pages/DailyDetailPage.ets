import router from '@ohos.router';
import storage from '@ohos.data.storage'; // 导入storage模块

interface GeneratedTypeLiteralInterface_1 {
  time: string;
  result: string;
  status: string;
}

interface GeneratedTypeLiteralInterface_2 {
  time: string;
  result: string;
  status: string;
}

@Entry
@Component
struct DailyDetailPage {
  private storage: storage.Storage | null = null; // 声明存储实例
  @State currentTime: string = this.getCurrentTime();
  @State lastUpdate: string = '2025-12-3 周三 12:01';
  @State todayChatCount: number = 8;
  @State todayChatDuration: number = 15;





  // 新增：获取登录时间（示例：当前时间）
  private getLoginTime(): string {
    const now = new Date();
    const hour = now.getHours().toString().padStart(2, '0');
    const minute = now.getMinutes().toString().padStart(2, '0');
    return `$ ${hour}:${minute}`;
  }



  build() {
    Column() {
      // 顶部标题栏
      Row() {
        Image($r('app.media.back_arrow'))
          .width(24)
          .height(24)
          .onClick(() => {
            router.back();
          })

        Text('今日详情')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .layoutWeight(1)
          .textAlign(TextAlign.Center)
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#007DFF')

      Scroll() {
        Column() {
          // 时间显示
          Text(this.currentTime)
            .fontSize(16)
            .fontColor('#666666')
            .margin({ top: 16, bottom: 8 })

          // 刷新按钮
          Row() {
            Text('最新数据')
              .fontSize(16)
              .fontColor('#FFFFFF')

            Text('点击这里')
              .fontSize(16)
              .fontColor('#FFF2CC')
              .fontWeight(FontWeight.Bold)
              .margin({ left: 4 })
          }
          .width('55%')
          .height(48)
          .backgroundColor('#FF6B35')
          .borderRadius(24)
          .justifyContent(FlexAlign.Center)
          .margin({ bottom: 8 })
          .onClick(() => {
            this.refreshData();
          })

          Text(`上次更新: ${this.lastUpdate}`)
            .fontSize(12)
            .fontColor('#999999')
            .margin({ bottom: 24 })

          // 语音摘要区域
          Row() {
            // 对话次数
            Column() {
              Text('今日语音摘要')
                .fontSize(14)
                .fontColor('#666666')
                .margin({ bottom: 8 })

              Text('查看语音交流统计')
                .fontSize(12)
                .fontColor('#999999')
                .margin({ bottom: 12 })

              Row() {
                Column() {
                  Text(this.todayChatCount.toString())
                    .fontSize(40)
                    .fontColor('#007DFF')
                    .fontWeight(FontWeight.Bold)

                  Text('今日对话次数')
                    .fontSize(12)
                    .fontColor('#666666')
                }
                .layoutWeight(1)


              }
            }
            .layoutWeight(1)
          }
          .width('100%')
          .padding(24)
          .backgroundColor(Color.White)
          .borderRadius(12)
          .margin({ bottom: 16 })


        }
        .width('100%')
        .padding(16)
      }
      .layoutWeight(0)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }

  private getStatusColor(status: string): string {
    switch (status) {
      case 'healthy': return '#4CAF50';
      case 'mild': return '#FF9800';
      case 'dementia': return '#F44336';
      default: return '#666666';
    }
  }

  // 获取当前时间
  private getCurrentTime(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    const date = now.getDate();
    const hour = now.getHours().toString().padStart(2, '0');
    const minute = now.getMinutes().toString().padStart(2, '0');
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekday = weekdays[now.getDay()];

    return `${year}-${month}-${date} ${weekday} ${hour}:${minute}`;
  }

  // 刷新数据：仅点击时更新lastUpdate为当前时间
  private refreshData(): void {
    const now = this.getCurrentTime();
    this.lastUpdate = now; // 更新@State（页面显示）
    // 新增功能：对话次数加1
    this.todayChatCount = this.todayChatCount + 1;

  }
}