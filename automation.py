#!/usr/bin/env python3


import csv
import sys
from datetime import datetime
from collections import Counter, defaultdict
import argparse

def parse_date(date_str):
    """解析多种日期格式"""
    if not date_str or date_str.strip() == '':
        return None
    
    date_str = date_str.strip()
    
    # 尝试不同的日期格式
    date_formats = [
        '%m/%d/%Y %I:%M:%S %p',  # 12/12/2025 3:30:19 PM
        '%Y-%m-%d %H:%M:%S',     # 2025-12-12 15:30:19
        '%m/%d/%Y',              # 12/12/2025
        '%Y-%m-%d'               # 2025-12-12
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    print(f"警告：无法解析日期: {date_str}")
    return None

def parse_csv_file(csv_file_path):
    """解析CSV文件并返回工作项数据"""
    work_items = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            # 使用DictReader按列名访问数据
            reader = csv.DictReader(file)
            
            # 检查必要的列是否存在
            required_columns = ['ID', 'Work Item Type', 'Title', 'State', 'Created Date']
            for col in required_columns:
                if col not in reader.fieldnames:
                    print(f"错误：CSV文件中缺少必需的列：{col}")
                    print(f"找到的列：{reader.fieldnames}")
                    return []
            
            print(f"找到的列：{list(reader.fieldnames)}")
            
            # 读取每一行数据
            for row_num, row in enumerate(reader, 1):
                try:
                    # 解析日期
                    created_date = parse_date(row['Created Date'])
                    closed_date = parse_date(row.get('Closed Date', ''))
                    
                    # 解析指派给（移除邮箱部分）
                    assigned_to = row.get('Assigned To', '').split('<')[0].strip() if row.get('Assigned To') else 'Unassigned'
                    
                    # 解析区域路径
                    area_path = row.get('Area Path', '')
                    
                    # 获取最后一部分作为团队/模块
                    if area_path:
                        area_parts = area_path.split('\\')
                        team = area_parts[-1] if area_parts else area_path
                    else:
                        team = 'Unknown'
                    
                    # 计算解决时间（如果已关闭）
                    resolution_time = None
                    if closed_date and created_date:
                        resolution_time = (closed_date - created_date).days
                    
                    # 解析Story Points
                    story_points = 0
                    try:
                        if row.get('Story Points'):
                            story_points = float(row['Story Points'])
                    except (ValueError, TypeError):
                        pass
                    
                    # 创建工作项对象
                    work_item = {
                        'id': row['ID'],
                        'type': row['Work Item Type'],
                        'title': row['Title'],
                        'assigned_to': assigned_to,
                        'state': row['State'],
                        'tags': row.get('Tags', '').split(';') if row.get('Tags') else [],
                        'created_date': created_date,
                        'priority': row.get('Priority', 'Not Set'),
                        'closed_date': closed_date,
                        'story_points': story_points,
                        'area_path': area_path,
                        'team': team,
                        'resolution_days': resolution_time
                    }
                    
                    work_items.append(work_item)
                    
                except KeyError as e:
                    print(f"警告：第{row_num}行缺少字段：{e}")
                except Exception as e:
                    print(f"警告：第{row_num}行解析失败：{e}")
                    print(f"行数据：{row}")
                    
        print(f"成功解析 {len(work_items)} 个工作项")
        return work_items
        
    except FileNotFoundError:
        print(f"错误：文件 '{csv_file_path}' 未找到")
        sys.exit(1)
    except PermissionError:
        print(f"错误：没有权限读取文件 '{csv_file_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"解析文件时发生错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def analyze_work_items(work_items):
    """分析工作项数据"""
    if not work_items:
        return {}
    
    analysis = {
        'total_items': len(work_items),
        'type_distribution': Counter(),
        'state_distribution': Counter(),
        'priority_distribution': Counter(),
        'team_distribution': Counter(),
        'assignee_distribution': Counter(),
        'open_items': [],
        'closed_items': [],
        'resolution_times': [],
        'story_points_total': 0,
        'story_points_by_team': defaultdict(float),
        'story_points_by_assignee': defaultdict(float),
        'story_points_by_type': defaultdict(float),
        'largest_story_items': [],
        'oldest_open_item': None,
        'newest_item': None
    }
    
    for item in work_items:
        # 基本统计
        analysis['type_distribution'][item['type']] += 1
        analysis['state_distribution'][item['state']] += 1
        analysis['priority_distribution'][item['priority']] += 1
        analysis['team_distribution'][item['team']] += 1
        analysis['assignee_distribution'][item['assigned_to']] += 1
        
        # Story Points统计
        story_points = item['story_points']
        analysis['story_points_total'] += story_points
        analysis['story_points_by_team'][item['team']] += story_points
        analysis['story_points_by_assignee'][item['assigned_to']] += story_points
        analysis['story_points_by_type'][item['type']] += story_points
        
        # 按状态分类
        if item['state'].lower() in ['new', 'active', 'open', 'in progress']:
            analysis['open_items'].append(item)
        elif item['state'].lower() in ['closed', 'resolved', 'done']:
            analysis['closed_items'].append(item)
            
            # 收集解决时间数据
            if item['resolution_days'] is not None:
                analysis['resolution_times'].append(item['resolution_days'])
        
        # 记录最大的Story Points项
        if story_points > 0:
            analysis['largest_story_items'].append({
                'id': item['id'],
                'title': item['title'],
                'story_points': story_points,
                'type': item['type'],
                'state': item['state'],
                'assigned_to': item['assigned_to'],
                'team': item['team']
            })
        
        # 日期相关分析
        if item['created_date']:
            if analysis['newest_item'] is None or item['created_date'] > analysis['newest_item']['date']:
                analysis['newest_item'] = {
                    'id': item['id'],
                    'date': item['created_date'],
                    'title': item['title'][:50] + '...' if len(item['title']) > 50 else item['title'],
                    'type': item['type'],
                    'story_points': story_points
                }
            
            # 如果是开放状态，检查是否为最旧的
            if item['state'].lower() in ['new', 'active', 'open', 'in progress']:
                if analysis['oldest_open_item'] is None or item['created_date'] < analysis['oldest_open_item']['date']:
                    age_days = (datetime.now() - item['created_date']).days
                    analysis['oldest_open_item'] = {
                        'id': item['id'],
                        'date': item['created_date'],
                        'title': item['title'][:50] + '...' if len(item['title']) > 50 else item['title'],
                        'age_days': age_days,
                        'priority': item['priority'],
                        'story_points': story_points
                    }
    
    # 计算解决时间统计
    if analysis['resolution_times']:
        analysis['avg_resolution_time'] = sum(analysis['resolution_times']) / len(analysis['resolution_times'])
        analysis['max_resolution_time'] = max(analysis['resolution_times'])
        analysis['min_resolution_time'] = min(analysis['resolution_times'])
    
    # 对最大的Story Points项进行排序
    analysis['largest_story_items'].sort(key=lambda x: x['story_points'], reverse=True)
    
    return analysis

def get_story_points_rankings(analysis, top_n=10):
    """生成Story Points排名"""
    rankings = {
        'by_assignee': [],
        'by_team': [],
        'by_type': [],
        'largest_items': analysis.get('largest_story_items', [])[:top_n]
    }
    
    # 按指派人排名
    if analysis.get('story_points_by_assignee'):
        for assignee, points in sorted(analysis['story_points_by_assignee'].items(), 
                                      key=lambda x: x[1], reverse=True)[:top_n]:
            item_count = analysis['assignee_distribution'][assignee]
            avg_points = points / item_count if item_count > 0 else 0
            rankings['by_assignee'].append({
                'name': assignee,
                'total_points': points,
                'item_count': item_count,
                'avg_points': avg_points
            })
    
    # 按团队排名
    if analysis.get('story_points_by_team'):
        for team, points in sorted(analysis['story_points_by_team'].items(), 
                                  key=lambda x: x[1], reverse=True)[:top_n]:
            item_count = analysis['team_distribution'][team]
            avg_points = points / item_count if item_count > 0 else 0
            rankings['by_team'].append({
                'name': team,
                'total_points': points,
                'item_count': item_count,
                'avg_points': avg_points
            })
    
    # 按类型排名
    if analysis.get('story_points_by_type'):
        for item_type, points in sorted(analysis['story_points_by_type'].items(), 
                                       key=lambda x: x[1], reverse=True):
            item_count = analysis['type_distribution'][item_type]
            avg_points = points / item_count if item_count > 0 else 0
            rankings['by_type'].append({
                'name': item_type,
                'total_points': points,
                'item_count': item_count,
                'avg_points': avg_points
            })
    
    return rankings

def generate_report(analysis):
    """生成分析报告"""
    if not analysis or analysis['total_items'] == 0:
        return "没有可分析的数据"
    
    # 获取Story Points排名
    rankings = get_story_points_rankings(analysis)
    
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("             Azure DevOps 工作项分析报告")
    report_lines.append("=" * 70)
    report_lines.append(f"总工作项数: {analysis['total_items']}")
    report_lines.append(f"开放项: {len(analysis['open_items'])} | 关闭项: {len(analysis['closed_items'])}")
    report_lines.append(f"总Story Points: {analysis['story_points_total']:.1f}")
    
    # 计算平均Story Points
    avg_story_points = analysis['story_points_total'] / analysis['total_items'] if analysis['total_items'] > 0 else 0
    report_lines.append(f"平均Story Points: {avg_story_points:.2f}")
    report_lines.append("")
    
    # Story Points排名部分
    report_lines.append("📊 STORY POINTS 排名分析")
    report_lines.append("=" * 50)
    
    # 按指派人排名
    if rankings['by_assignee']:
        report_lines.append("\n按指派人Story Points排名 (前10名):")
        report_lines.append("-" * 60)
        report_lines.append(f"{'排名':<4} {'指派人':<20} {'总点数':<10} {'工作项数':<10} {'平均点数':<10}")
        report_lines.append("-" * 60)
        
        for i, assignee_data in enumerate(rankings['by_assignee'][:10], 1):
            report_lines.append(
                f"{i:<4} {assignee_data['name']:<20} "
                f"{assignee_data['total_points']:<10.1f} "
                f"{assignee_data['item_count']:<10} "
                f"{assignee_data['avg_points']:<10.2f}"
            )
    
    # 按团队排名
    if rankings['by_team']:
        report_lines.append("\n按团队Story Points排名 (前10名):")
        report_lines.append("-" * 60)
        report_lines.append(f"{'排名':<4} {'团队':<25} {'总点数':<10} {'工作项数':<10} {'平均点数':<10}")
        report_lines.append("-" * 60)
        
        for i, team_data in enumerate(rankings['by_team'][:10], 1):
            report_lines.append(
                f"{i:<4} {team_data['name']:<25} "
                f"{team_data['total_points']:<10.1f} "
                f"{team_data['item_count']:<10} "
                f"{team_data['avg_points']:<10.2f}"
            )
    
    # 按类型排名
    if rankings['by_type']:
        report_lines.append("\n按类型Story Points排名:")
        report_lines.append("-" * 45)
        report_lines.append(f"{'类型':<15} {'总点数':<10} {'工作项数':<10} {'平均点数':<10}")
        report_lines.append("-" * 45)
        
        for type_data in rankings['by_type']:
            report_lines.append(
                f"{type_data['name']:<15} "
                f"{type_data['total_points']:<10.1f} "
                f"{type_data['item_count']:<10} "
                f"{type_data['avg_points']:<10.2f}"
            )
    
    # 最大的Story Points项
    if rankings['largest_items']:
        report_lines.append("\n🔝 最大的Story Points工作项 (前10名):")
        report_lines.append("-" * 70)
        report_lines.append(f"{'排名':<4} {'ID':<10} {'点数':<8} {'类型':<10} {'状态':<12} {'指派人':<15} {'标题'}")
        report_lines.append("-" * 70)
        
        for i, item in enumerate(rankings['largest_items'][:10], 1):
            title_display = item['title'][:30] + '...' if len(item['title']) > 30 else item['title']
            report_lines.append(
                f"{i:<4} {item['id']:<10} "
                f"{item['story_points']:<8.1f} "
                f"{item['type']:<10} "
                f"{item['state']:<12} "
                f"{item['assigned_to'][:14]:<15} "
                f"{title_display}"
            )
    
    report_lines.append("\n" + "=" * 70)
    report_lines.append("📈 基本统计信息")
    report_lines.append("=" * 50)
    
    # 工作项类型分布
    report_lines.append("\n工作项类型分布:")
    report_lines.append("-" * 35)
    for item_type, count in analysis['type_distribution'].most_common():
        percentage = (count / analysis['total_items']) * 100
        points_percentage = (analysis['story_points_by_type'][item_type] / analysis['story_points_total'] * 100) if analysis['story_points_total'] > 0 else 0
        report_lines.append(f"  {item_type:<15} {count:>3} ({percentage:>5.1f}%) | 点数: {analysis['story_points_by_type'][item_type]:>5.1f} ({points_percentage:>5.1f}%)")
    report_lines.append("")
    
    # 状态分布
    report_lines.append("状态分布:")
    report_lines.append("-" * 35)
    for state, count in analysis['state_distribution'].most_common():
        percentage = (count / analysis['total_items']) * 100
        report_lines.append(f"  {state:<15} {count:>3} ({percentage:>5.1f}%)")
    report_lines.append("")
    
    # 优先级分布
    report_lines.append("优先级分布:")
    report_lines.append("-" * 35)
    for priority, count in sorted(analysis['priority_distribution'].items(), 
                                  key=lambda x: int(x[0]) if x[0].isdigit() else 999):
        percentage = (count / analysis['total_items']) * 100
        report_lines.append(f"  Priority {priority:<5} {count:>3} ({percentage:>5.1f}%)")
    report_lines.append("")
    
    # 解决时间统计
    if 'avg_resolution_time' in analysis:
        report_lines.append("解决时间统计 (已关闭项目):")
        report_lines.append("-" * 35)
        report_lines.append(f"  平均解决时间: {analysis['avg_resolution_time']:.1f} 天")
        report_lines.append(f"  最长解决时间: {analysis['max_resolution_time']} 天")
        report_lines.append(f"  最短解决时间: {analysis['min_resolution_time']} 天")
        report_lines.append(f"  总关闭项数: {len(analysis['closed_items'])}")
        report_lines.append("")
    
    # 最旧的开放项
    if analysis['oldest_open_item']:
        oldest = analysis['oldest_open_item']
        report_lines.append("最旧的开放工作项:")
        report_lines.append("-" * 35)
        report_lines.append(f"  ID: {oldest['id']}")
        report_lines.append(f"  创建时间: {oldest['date'].strftime('%Y-%m-%d')}")
        report_lines.append(f"  已开放天数: {oldest['age_days']} 天")
        report_lines.append(f"  优先级: {oldest['priority']}")
        report_lines.append(f"  Story Points: {oldest['story_points']}")
        report_lines.append(f"  标题: {oldest['title']}")
        report_lines.append("")
    
    # 最新项
    if analysis['newest_item']:
        newest = analysis['newest_item']
        report_lines.append("最新创建的工作项:")
        report_lines.append("-" * 35)
        report_lines.append(f"  ID: {newest['id']}")
        report_lines.append(f"  类型: {newest['type']}")
        report_lines.append(f"  创建时间: {newest['date'].strftime('%Y-%m-%d %H:%M')}")
        report_lines.append(f"  Story Points: {newest['story_points']}")
        report_lines.append(f"  标题: {newest['title']}")
    
    report_lines.append("=" * 70)
    
    return "\n".join(report_lines)

def generate_sample_csv():
    """生成符合实际格式的示例CSV"""
    sample_csv = """ID,Work Item Type,Title,Assigned To,State,Tags,Created Date,Priority,Closed Date,Story Points,Area Path
"79906","Bug","Ads tool tip not showing correctly","Jason Lin <jalin@lifetime.com>","Closed",,"12/12/2025 3:30:19 PM","2","12/15/2025 12:53:54 PM","1","Lifetime Applications\External\Web\Valas"
"79907","Task","Update documentation for API v2","Sarah Chen <schen@lifetime.com>","In Progress","documentation;api","12/10/2025 10:15:00 AM","3",,"3","Lifetime Applications\Internal\Web\API"
"79908","Bug","Login page crashes on mobile","Mike Johnson <mjohnson@lifetime.com>","New","urgent;mobile","12/16/2025 9:45:00 AM","1",,"2","Lifetime Applications\External\Web\Valas"
"79909","User Story","Implement user profile page","Alex Wang <awang@lifetime.com>","Closed","ui;profile","12/01/2025 2:00:00 PM","2","12/10/2025 4:30:00 PM","8","Lifetime Applications\External\Mobile"
"79910","Bug","Database connection timeout","Jason Lin <jalin@lifetime.com>","Resolved","database","12/05/2025 11:20:00 AM","1","12/07/2025 3:15:00 PM","3","Lifetime Applications\Internal\Services"
"79911","Task","Code review for PR #456","Sarah Chen <schen@lifetime.com>","New","code-review","12/15/2025 4:30:00 PM","3",,"2","Lifetime Applications\Internal\Web\API"
"79912","Bug","CSS alignment issue in Firefox","Mike Johnson <mjohnson@lifetime.com>","Closed","css;firefox","12/08/2025 2:45:00 PM","2","12/09/2025 11:30:00 AM","1","Lifetime Applications\External\Web\Valas"
"79913","User Story","Add search functionality","Alex Wang <awang@lifetime.com>","In Progress","search;feature","12/03/2025 9:00:00 AM","2",,"13","Lifetime Applications\External\Mobile"
"79914","Task","Setup CI/CD pipeline","David Kim <dkim@lifetime.com>","Done","devops;ci-cd","11/25/2025 1:15:00 PM","3","12/05/2025 5:00:00 PM","5","Lifetime Applications\Internal\DevOps"
"79915","Bug","Memory leak in analytics module","Jason Lin <jalin@lifetime.com>","Active","memory;analytics","12/14/2025 3:00:00 PM","1",,"2","Lifetime Applications\External\Web\Valas"
"79916","User Story","Redesign dashboard UI","Emma Wilson <ewilson@lifetime.com>","Closed","ui;dashboard","12/02/2025 10:00:00 AM","2","12/12/2025 3:00:00 PM","5","Lifetime Applications\External\Web\Valas"
"79917","Task","Update dependencies","Tom Brown <tbrown@lifetime.com>","New","maintenance","12/17/2025 11:00:00 AM","3",,"1","Lifetime Applications\Internal\Services"
"79918","Bug","Performance issue on checkout","Jason Lin <jalin@lifetime.com>","Active","performance","12/13/2025 2:30:00 PM","1",,"3","Lifetime Applications\External\Web\Valas"
"79919","User Story","Implement payment gateway","Sarah Chen <schen@lifetime.com>","In Progress","payment;feature","12/05/2025 9:30:00 AM","2",,"8","Lifetime Applications\External\Mobile"
"79920","Task","Write unit tests for auth module","Mike Johnson <mjohnson@lifetime.com>","New","testing","12/16/2025 3:00:00 PM","3",,"3","Lifetime Applications\Internal\Web\API"""
    
    return sample_csv

def save_sample_csv(filename="azure_devops_sample.csv"):
    """保存示例CSV文件"""
    sample_data = generate_sample_csv()
    
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(sample_data)
        print(f"示例CSV文件已保存为: {filename}")
        print(f"使用命令测试: python azure_analyzer.py {filename}")
        return filename
    except Exception as e:
        print(f"保存示例文件失败: {e}")
        return None

def export_story_points_analysis(analysis, filename="story_points_analysis.csv"):
    """导出Story Points分析报告"""
    if not analysis or analysis['total_items'] == 0:
        print("没有数据可导出")
        return False
    
    try:
        rankings = get_story_points_rankings(analysis)
        
        with open(filename, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            
            # 写入标题
            writer.writerow(["Story Points 详细分析报告"])
            writer.writerow([])
            
            # 汇总信息
            writer.writerow(["汇总信息"])
            writer.writerow(["总工作项数", analysis['total_items']])
            writer.writerow(["总Story Points", f"{analysis['story_points_total']:.2f}"])
            writer.writerow(["平均Story Points", f"{analysis['story_points_total']/analysis['total_items']:.2f}"])
            writer.writerow([])
            
            # 按指派人排名
            writer.writerow(["按指派人Story Points排名"])
            writer.writerow(["排名", "指派人", "总点数", "工作项数", "平均点数"])
            for i, assignee_data in enumerate(rankings['by_assignee'], 1):
                writer.writerow([
                    i,
                    assignee_data['name'],
                    f"{assignee_data['total_points']:.2f}",
                    assignee_data['item_count'],
                    f"{assignee_data['avg_points']:.2f}"
                ])
            writer.writerow([])
            
            # 按团队排名
            writer.writerow(["按团队Story Points排名"])
            writer.writerow(["排名", "团队", "总点数", "工作项数", "平均点数"])
            for i, team_data in enumerate(rankings['by_team'], 1):
                writer.writerow([
                    i,
                    team_data['name'],
                    f"{team_data['total_points']:.2f}",
                    team_data['item_count'],
                    f"{team_data['avg_points']:.2f}"
                ])
            writer.writerow([])
            
            # 最大的Story Points项
            writer.writerow(["最大的Story Points工作项"])
            writer.writerow(["排名", "ID", "点数", "类型", "状态", "指派人", "团队", "标题"])
            for i, item in enumerate(rankings['largest_items'][:20], 1):
                writer.writerow([
                    i,
                    item['id'],
                    f"{item['story_points']:.1f}",
                    item['type'],
                    item['state'],
                    item['assigned_to'],
                    item['team'],
                    item['title']
                ])
        
        print(f"Story Points分析报告已导出到: {filename}")
        return True
        
    except Exception as e:
        print(f"导出Story Points分析报告失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Azure DevOps工作项分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s data.csv                    # 分析CSV文件
  %(prog)s --sample                    # 生成示例文件
  %(prog)s data.csv --story-points-report  # 导出Story Points分析报告
        """
    )
    
    parser.add_argument('csv_file', nargs='?', help='CSV文件路径')
    parser.add_argument('--sample', action='store_true', help='生成示例CSV文件')
    parser.add_argument('--story-points-report', metavar='FILE', 
                       help='导出Story Points分析报告到指定文件')
    parser.add_argument('--top-n', type=int, default=10, 
                       help='显示前N名排名 (默认: 10)')
    
    args = parser.parse_args()
    
    # 生成示例文件
    if args.sample:
        filename = save_sample_csv()
        if filename:
            print("\n示例文件内容预览:")
            print("-" * 40)
            lines = generate_sample_csv().split('\n')[:5]
            for line in lines:
                print(line)
        return
    
    # 检查文件参数
    if not args.csv_file:
        print("请提供CSV文件路径")
        parser.print_help()
        return
    
    print(f"开始分析文件: {args.csv_file}")
    print("-" * 50)
    
    # 解析CSV文件
    work_items = parse_csv_file(args.csv_file)
    
    if not work_items:
        print("没有解析到有效的工作项数据")
        return
    
    # 分析数据
    print("正在分析数据...")
    analysis = analyze_work_items(work_items)
    
    # 生成报告
    report = generate_report(analysis)
    
    # 输出报告
    print("\n" + report)
    
    # 导出Story Points分析报告
    if args.story_points_report:
        export_story_points_analysis(analysis, args.story_points_report)
    
    # 提供基于Story Points的建议
    print("\n📋 基于Story Points的分析建议:")
    print("-" * 50)
    
    total_points = analysis['story_points_total']
    open_items = analysis['open_items']
    
    if open_items:
        open_points = sum(item['story_points'] for item in open_items)
        open_percentage = (open_points / total_points * 100) if total_points > 0 else 0
        
        print(f"📊 当前开放项Story Points: {open_points:.1f} ({open_percentage:.1f}% of total)")
        
        # 按指派人分析开放项点数
        print("\n按指派人开放项Story Points分布:")
        assignee_open_points = defaultdict(float)
        for item in open_items:
            assignee_open_points[item['assigned_to']] += item['story_points']
        
        for assignee, points in sorted(assignee_open_points.items(), key=lambda x: x[1], reverse=True):
            print(f"  {assignee}: {points:.1f} points")
        
        # 检查是否有过载的指派人
        avg_open_points = open_points / len(assignee_open_points) if assignee_open_points else 0
        for assignee, points in assignee_open_points.items():
            if points > avg_open_points * 2:
                print(f"⚠️  {assignee} 的开放项点数 ({points:.1f}) 明显高于平均 ({avg_open_points:.1f})")
    
    # 检查最大的开放项
    largest_open_items = sorted([item for item in open_items if item['story_points'] > 0], 
                               key=lambda x: x['story_points'], reverse=True)[:3]
    
    if largest_open_items:
        print("\n🔝 最大的开放项 (按Story Points):")
        for item in largest_open_items:
            print(f"  {item['id']}: {item['title'][:40]}... ({item['story_points']} points)")

if __name__ == "__main__":
    main()