import router from '@ohos.router';
import storage from '@ohos.data.storage'; // 导入storage模块


@Entry
@Component
struct HomePage {
  @State currentTime: string = this.getCurrentTime();
  @State lastUpdate: string = '2025-12-3 周三 12:01';

  // 模拟数据
  @State todaySummary: string = '查看语音交流统计';
  @State todayEvaluationCount: number = 4;
  @State careReminders: number = 1;
  @State careMessage: string = '今日交流正常，老人情绪稳定。';

  private getLoginTime(): string {
    const now = new Date();
    const hour = now.getHours().toString().padStart(2, '0');
    const minute = now.getMinutes().toString().padStart(2, '0');
    return `$ ${hour}:${minute}`;
  }



  build() {
    Column() {
      // ---------- 顶部标题栏 ----------
      Row() {
        // 返回按钮
        Image($r('app.media.back_arrow'))
          .width(24)
          .height(24)
          .onClick(() => {
            router.back();
          })

        Text('关爱·守护')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .layoutWeight(1)
          .textAlign(TextAlign.Center)

        Text('子女')
          .fontSize(14)
          .fontColor(Color.White)
          .backgroundColor('#FF9800')
          .padding({ left: 8, right: 8, top: 4, bottom: 4 })
          .borderRadius(12)
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#007DFF')

      // ---------- 时间显示 ----------
      Text(this.currentTime)
        .fontSize(16)
        .fontColor('#666666')
        .margin({ top: 16, bottom: 8 })

      // ---------- 刷新数据按钮 ----------
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

      Text(`上一次更新：${this.lastUpdate}`)
        .fontSize(12)
        .fontColor('#999999')
        .margin({ bottom: 10 })

      // ---------- 内容卡片区域 ----------
      Scroll() {
        Column() {
          // 卡片1：今日语音摘要
          this.buildInfoCard(
            $r('app.media.chat_icon'),
            '今日语音摘要',
            this.todaySummary,
            '#FF9800',
            'pages/DailyDetailPage'
          )

          // 卡片2：今日预测结果
          this.buildInfoCard(
            $r('app.media.brain_icon'),
            '今日老年痴呆预测结果',
            `共${this.todayEvaluationCount}次评测`,
            '#4CAF50',
            'pages/TodayPage'
          )

          // 卡片3：七日预测结果
          this.buildInfoCard(
            $r('app.media.calendar_icon'),
            '老年痴呆七日综合预测结果',
            '点击查看详细统计',
            '#2196F3',
            'pages/WeeklyReportPage'
          )

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

  @Builder
  buildInfoCard(icon: Resource, title: string, content: string, color: string, targetPage: string) {
    Column() {
      Row() {
        Image(icon)
          .width(20)
          .height(20)
          .margin({ right: 8 })

        Text(title)
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .fontColor('#182431')
          .layoutWeight(1)
      }
      .width('100%')
      .margin({ bottom: 12 })

      Text(content)
        .fontSize(14)
        .fontColor('#666666')
        .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .margin({ bottom: 16 })
    .onClick(() => {
      router.pushUrl({ url: targetPage });
    })
  }

  @Builder
  buildCareCard() {
    Column() {
      Row() {
        Image($r('app.media.heart_icon'))
          .width(20)
          .height(20)
          .margin({ right: 8 })

        Text('今日关怀提醒')
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .fontColor('#182431')
          .layoutWeight(1)

        Text(`${this.careReminders}条提醒`)
          .fontSize(12)
          .fontColor('#FF6B35')
          .backgroundColor('#FFE8E0')
          .padding(4)
          .borderRadius(4)
      }
      .width('100%')
      .margin({ bottom: 12 })

      Row() {
        Text('i')
          .fontSize(14)
          .fontColor('#2196F3')
          .backgroundColor('#E3F2FD')
          .width(20)
          .height(20)
          .borderRadius(10)
          .textAlign(TextAlign.Center)
          .margin({ right: 8 })

        Text(this.careMessage)
          .fontSize(14)
          .fontColor('#2196F3')
          .layoutWeight(1)
      }
      .width('100%')
      .padding(12)
      .backgroundColor('#E3F2FD')
      .borderRadius(8)
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
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

  // 刷新数据
  private refreshData(): void {
    const now = this.getCurrentTime();
    this.lastUpdate = now; // 更新@State（页面显示）

  }
}